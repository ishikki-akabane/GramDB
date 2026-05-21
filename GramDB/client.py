"""
GramDB Core Client Implementation.
"""

from __future__ import annotations


import asyncio
import logging
import os
import uuid
from typing import Any

import aiohttp

from GramDB.config import parse_database_url
from GramDB.engine.query import EfficientDictQuery
from GramDB.exception import GramDBError, GramDBTelegramError
from GramDB.persistence import PersistenceManager, SyncOp, WriteAheadLog
from GramDB.registry.client import RegistryClient
from GramDB.telegram.cold_store_v2 import TelegramColdStoreV2
from GramDB.telegram.pyrogram_pool import PyrogramWorkerPool
from GramDB.utils.canonical_json import dumps_canonical

logger = logging.getLogger("GramDB")


class GramDB:
    """
    Async GramDB client: metadata and session lease from the registry API, row
    storage in a private Telegram channel via Pyrogram (rotating bot workers).
    """

    def __init__(
        self,
        database_url: str,
        bot_tokens: str | list[str],
        api_id: int, api_hash: str,
        *,
        http_session: aiohttp.ClientSession | None = None,
    ) -> None:
        if isinstance(bot_tokens, str):
            bot_tokens = [bot_tokens]
        self._database_url = database_url.strip()
        self._bot_tokens = list(bot_tokens)
        self._api_id = api_id
        self._api_hash = api_hash
        self._http_external = http_session is not None
        self._http = http_session
        self._resolved = parse_database_url(self._database_url)
        self._registry = RegistryClient(self._resolved)

        self._pool: PyrogramWorkerPool | None = None
        self._cold: TelegramColdStoreV2 | None = None
        self._engine: EfficientDictQuery | None = None
        self._metadata: dict[str, Any] = {}

        self._instance_id = str(uuid.uuid4())
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._pm: PersistenceManager | None = None
        self._wal: WriteAheadLog | None = None
        self._connected = False
        self._write_lock = asyncio.Lock()

        if len(self._bot_tokens) < 2:
            logger.warning(
                "Using fewer than two bot tokens increases flood-wait risk; "
                "add every bot as channel admin and pass at least two tokens."
            )

    @property
    def connected(self) -> bool:
        return self._connected

    async def connect(self, *, client_label: str | None = None) -> None:
        """
        Connect to the GramDB registry and initialize storage workers.
        """

        if self._connected:
            raise GramDBError("GramDB client is already connected")

        if self._http is None:
            self._http = aiohttp.ClientSession()

        lease_acquired = False
        api_token: str | None = None
        try:
            meta = await self._registry.fetch_metadata(self._http)
            self._metadata = meta

            token = meta.get("api_token")
            if not token or not isinstance(token, str):
                raise GramDBError("registry metadata missing api_token")
            api_token = token

            if meta.get("locked"):
                raise GramDBError(f"database is locked: {meta.get('locked_reason')}")

            channel_id = meta.get("channel_id")
            if channel_id is None:
                raise GramDBError("registry metadata missing channel_id")
            channel_id = int(channel_id)

            index_message_id = meta.get("index_message_id")
            if index_message_id is not None:
                index_message_id = int(index_message_id)
                if index_message_id <= 0:
                    index_message_id = None

            hb = float(meta.get("heartbeat_interval_seconds", 15))

            await self._registry.acquire_session(
                self._http,
                api_token=api_token,
                instance_id=self._instance_id,
                client_label=client_label,
            )
            lease_acquired = True

            self._pool = PyrogramWorkerPool(self._bot_tokens, self._api_id, self._api_hash)
            await self._pool.start()
            await self._pool.ensure_channel_admin(channel_id)

            if index_message_id is None:
                root_mid = await self._bootstrap_v2_root(channel_id=channel_id, compaction_every=50)
                index_message_id = root_mid
                await self._registry.report_index_message_id(
                    self._http, api_token=api_token, index_message_id=root_mid
                )

            assert index_message_id is not None
            self._cold = TelegramColdStoreV2(self._pool, channel_id, int(index_message_id))
            try:
                await self._cold.ensure_root_initialized(compaction_every=50)
            except Exception:
                root_mid = await self._bootstrap_v2_root(channel_id=channel_id, compaction_every=50)
                await self._registry.report_index_message_id(
                    self._http, api_token=api_token, index_message_id=root_mid
                )
                self._cold = TelegramColdStoreV2(self._pool, channel_id, int(root_mid))
                await self._cold.ensure_root_initialized(compaction_every=50)

            wal_path = os.getenv("GRAMDB_WAL_PATH", os.path.join(os.getcwd(), "journal.json"))
            self._wal = WriteAheadLog(wal_path)

            async def apply_batch(batch: list[SyncOp]) -> None:
                assert self._cold is not None
                ops: list[dict[str, Any]] = []
                for b in batch:
                    payload = dict(b.payload or {})
                    payload["op_id"] = b.op_id
                    payload["kind"] = b.kind
                    payload["table"] = b.table
                    if b.row_uuid is not None:
                        payload["row_uuid"] = b.row_uuid
                    ops.append(payload)
                if not batch:
                    return
                try:
                    assert self._wal is not None
                    await self._cold.apply_batch(ops, table=batch[0].table, patch=self._wal.patch)
                except Exception as e:  # noqa: BLE001
                    msg = str(e)
                    if "403" in msg or "401" in msg or "Forbidden" in msg or "Unauthorized" in msg:
                        if self._http and api_token:
                            await self._registry.lock_database(self._http, api_token=api_token, reason=msg[:200])
                    raise

            self._pm = PersistenceManager(wal=self._wal, apply_batch=apply_batch, batch_window_ms=200)
            await self._pm.start()
            await self._hydrate_engine()
            pending = await self._wal.load_pending()
            await self._replay_ops_to_hot_cache(pending)
            await self._pm.recover_from_wal()

            self._heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(api_token=api_token, interval=hb),
                name="gramdb-heartbeat",
            )
            self._connected = True
            logger.info("GramDB connected (%s)", self._resolved.client_key)
        except Exception:
            if lease_acquired and self._http and api_token:
                try:
                    await self._registry.release_session(
                        self._http,
                        api_token=api_token,
                        instance_id=self._instance_id,
                    )
                except Exception:  # noqa: BLE001
                    logger.exception("failed to release session after partial connect")
            if self._pool:
                await self._pool.stop()
                self._pool = None
            if self._pm:
                await self._pm.stop()
                self._pm = None
            self._wal = None
            self._cold = None
            self._engine = None
            if self._http and not self._http_external:
                await self._http.close()
                self._http = None
            raise

    async def _heartbeat_loop(self, *, api_token: str, interval: float) -> None:
        try:
            while True:
                await asyncio.sleep(max(3.0, interval))
                if not self._http:
                    break
                await self._registry.heartbeat(
                    self._http,
                    api_token=api_token,
                    instance_id=self._instance_id,
                )
        except asyncio.CancelledError:
            return
        except Exception:  # noqa: BLE001
            logger.exception("heartbeat loop crashed")

    async def _hydrate_engine(self) -> None:
        assert self._cold is not None
        rows_list = await self._cold.hydrate_all_rows()
        rows: dict[str, dict[str, Any]] = {}
        for r in rows_list:
            if not isinstance(r, dict):
                continue
            mid = r.get("_m_id")
            if not isinstance(mid, str) or not mid:
                continue
            if "_table_" not in r or "_id" not in r:
                continue
            rows[mid] = r
        self._engine = EfficientDictQuery(rows)

    async def _reload_engine_from_channel(self) -> None:
        await self._hydrate_engine()

    def _require_engine(self) -> EfficientDictQuery:
        if not self._engine:
            raise GramDBError("GramDB is not connected")
        return self._engine

    async def close(self) -> None:
        logger.info("Stopping GramDB, please wait...")
        if self._pm:
            if self._pm.frozen:
                raise GramDBError(f"cannot flush pending writes: {self._pm.frozen_reason}")
            logger.info("Flushing pending writes to Telegram...")
            await self._pm.flush()
            logger.info("Flush complete.")
            await self._pm.stop()
            self._pm = None
        self._wal = None
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

        api_token = self._metadata.get("api_token") if isinstance(self._metadata, dict) else None
        if self._http and api_token:
            try:
                await self._registry.release_session(
                    self._http,
                    api_token=str(api_token),
                    instance_id=self._instance_id,
                )
            except Exception:  # noqa: BLE001
                logger.exception("session release failed")

        if self._pool:
            await self._pool.stop()
            self._pool = None

        if self._http and not self._http_external:
            await self._http.close()
            self._http = None
        self._cold = None
        self._engine = None
        self._connected = False
        logger.info("GramDB closed")

    async def __aenter__(self) -> GramDB:
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        await self.close()

    # --- CRUD (aliases match older GramDB examples) ---

    async def check_table(self, table_name: str) -> bool:
        return await self._require_engine().check_table(table_name)

    async def create_one(self, table_name: str, schema: list[str] | tuple[str, ...]) -> None:
        async with self._write_lock:
            eng = self._require_engine()
            sample_record: dict[str, Any] = {field: "gramdb" for field in schema}
            sample_record["_id"] = "sample1728"
            row_uuid = str(uuid.uuid4())
            sample_record["_m_id"] = row_uuid
            await eng.create(table_name, schema, dict(sample_record), row_uuid)
            if not self._pm:
                raise GramDBError("persistence manager is not running")
            await self._pm.enqueue(
                SyncOp(
                    op_id=str(uuid.uuid4()),
                    kind="table_create",
                    table=table_name,
                    row_uuid=None,
                    payload={"schema": list(schema)},
                )
            )
            tg_row = dict(sample_record)
            tg_row["_table_"] = table_name
            await self._pm.enqueue(
                SyncOp(
                    op_id=str(uuid.uuid4()),
                    kind="row_upsert",
                    table=table_name,
                    row_uuid=row_uuid,
                    payload={"row": tg_row},
                )
            )

    async def insert_one(self, table_name: str, record: dict[str, Any]) -> None:
        async with self._write_lock:
            eng = self._require_engine()
            rec = dict(record)
            if "_id" not in rec:
                rec["_id"] = await eng._generate_random_id()  # noqa: SLF001
            row_uuid = str(uuid.uuid4())
            await eng.insert_one(table_name, rec, _m_id=row_uuid)
            rec["_m_id"] = row_uuid
            if not self._pm:
                raise GramDBError("persistence manager is not running")
            tg_row = dict(rec)
            tg_row["_table_"] = table_name
            await self._pm.enqueue(
                SyncOp(
                    op_id=str(uuid.uuid4()),
                    kind="row_upsert",
                    table=table_name,
                    row_uuid=row_uuid,
                    payload={"row": tg_row},
                )
            )

    async def find(self, table_name: str, query: dict[str, Any]) -> list[dict[str, Any]]:
        return await self._require_engine().fetch(table_name, query)

    async def find_one(self, table_name: str, query: dict[str, Any]) -> dict[str, Any] | None:
        rows = await self.find(table_name, query)
        return rows[0] if rows else None

    async def find_all(self, table: str | None = None) -> Any:
        return await self._require_engine().fetch_all(table)

    async def update_one(
        self, table_name: str, query: dict[str, Any], update_query: dict[str, Any]
    ) -> None:
        async with self._write_lock:
            eng = self._require_engine()
            row_uuid, _old_id = await eng.update_one(table_name, query, update_query)
            rows = await eng.fetch(table_name, {"_id": _old_id})
            if not rows:
                raise GramDBError("failed to read row after update")
            row = dict(rows[0])
            if not self._pm:
                raise GramDBError("persistence manager is not running")
            tg_row = dict(row)
            tg_row["_table_"] = table_name
            await self._pm.enqueue(
                SyncOp(
                    op_id=str(uuid.uuid4()),
                    kind="row_upsert",
                    table=table_name,
                    row_uuid=str(row_uuid),
                    payload={"row": tg_row},
                )
            )

    async def delete_one(self, table_name: str, query: dict[str, Any]) -> None:
        async with self._write_lock:
            eng = self._require_engine()
            rows = await eng.fetch(table_name, query)
            if not rows:
                raise ValueError(f"No records found matching query: {query}")
            record_id = rows[0].get("_id")
            row_uuid = rows[0].get("_m_id")
            if not isinstance(record_id, str) or not isinstance(row_uuid, str):
                raise GramDBError("invalid record metadata for delete")
            await eng.delete_one(table_name, query)
            if not self._pm:
                raise GramDBError("persistence manager is not running")
            await self._pm.enqueue(
                SyncOp(
                    op_id=str(uuid.uuid4()),
                    kind="row_delete",
                    table=table_name,
                    row_uuid=str(row_uuid),
                    payload={"_id": record_id},
                )
            )

    async def delete_table(self, table_name: str) -> None:
        async with self._write_lock:
            eng = self._require_engine()
            await eng.delete_table(table_name)
            if not self._pm:
                raise GramDBError("persistence manager is not running")
            await self._pm.enqueue(
                SyncOp(
                    op_id=str(uuid.uuid4()),
                    kind="table_drop",
                    table=table_name,
                    row_uuid=None,
                    payload={},
                )
            )

    async def wait_for_background_tasks(self) -> None:
        if self._pm:
            await self._pm.flush()

    # --- legacy names used in older scripts ---

    create = create_one
    insert = insert_one
    fetch = find
    update = update_one
    delete = delete_one

    @staticmethod
    async def create_client(
        database_url: str,
        bot_tokens: str | list[str],
        *,
        api_id: int,
        api_hash: str,
        client_label: str | None = None,
        http_session: aiohttp.ClientSession | None = None,
    ) -> GramDB:
        g = GramDB(database_url, bot_tokens, api_id, api_hash, http_session=http_session)
        await g.connect(client_label=client_label)
        return g

    async def _bootstrap_v2_root(self, *, channel_id: int, compaction_every: int) -> int:
        assert self._pool is not None
        root = {"v": 2, "tables": {}, "compaction_every": int(compaction_every)}
        text = dumps_canonical(root)

        async def work(c):  # noqa: ANN001
            m = await c.send_message(channel_id, text)
            return int(m.id)

        return await self._pool.execute_primary(work)

    async def _replay_ops_to_hot_cache(self, ops: list[SyncOp]) -> None:
        if not ops:
            return
        eng = self._require_engine()
        for op in ops:
            if op.kind == "row_upsert":
                row = op.payload.get("row") if isinstance(op.payload, dict) else None
                if not isinstance(row, dict):
                    continue
                table = op.table
                if row.get("_table_") != table:
                    continue
                record_id = row.get("_id")
                row_uuid = row.get("_m_id")
                if not isinstance(record_id, str) or not isinstance(row_uuid, str):
                    continue
                body = dict(row)
                body.pop("_table_", None)
                exists = await eng.fetch(table, {"_id": record_id})
                if not exists:
                    try:
                        await eng.insert_one(table, body, _m_id=row_uuid)
                    except Exception:
                        continue
                else:
                    try:
                        await eng.update_one(table, {"_id": record_id}, {"$set": body})
                    except Exception:
                        continue
            elif op.kind == "row_delete":
                record_id = op.payload.get("_id") if isinstance(op.payload, dict) else None
                if not isinstance(record_id, str):
                    continue
                try:
                    await eng.delete_one(op.table, {"_id": record_id})
                except Exception:
                    continue
