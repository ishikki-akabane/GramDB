from __future__ import annotations

import hashlib
import time
from typing import Any

from GramDB.utils.pyrogram_logging import configure_pyrogram_logging

configure_pyrogram_logging()

from pyrogram import Client

from GramDB.telegram.page_codec import decode_page, encode_page
from GramDB.telegram.pyrogram_pool import PyrogramWorkerPool
from GramDB.utils.canonical_json import dumps_canonical
from GramDB.utils.json_codec import loads_safe
from GramDB.utils.telegram_payload import MAX_SAFE_MESSAGE_BYTES


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _split_text_pages(*, text: str, parent_id: str, max_bytes: int) -> list[str]:
    if max_bytes <= 64:
        raise ValueError("max_bytes too small")

    enc = text.encode("utf-8")
    if len(enc) <= max_bytes:
        return [encode_page(current=1, total=1, parent_id=parent_id, payload=text)]

    chunks: list[str] = []
    buf: list[str] = []
    buf_bytes = 0

    for ch in text:
        b = len(ch.encode("utf-8"))
        if buf and buf_bytes + b > max_bytes:
            chunks.append("".join(buf))
            buf = [ch]
            buf_bytes = b
        else:
            buf.append(ch)
            buf_bytes += b

    if buf:
        chunks.append("".join(buf))

    total = len(chunks)
    return [
        encode_page(current=i + 1, total=total, parent_id=parent_id, payload=payload)
        for i, payload in enumerate(chunks)
    ]


class TelegramColdStoreV2:
    def __init__(self, pool: PyrogramWorkerPool, channel_id: int, root_message_id: int) -> None:
        self.pool = pool
        self.channel_id = channel_id
        self.root_message_id = int(root_message_id)
        self._root_lock = pool._lock  # noqa: SLF001

    async def _send_text(self, text: str) -> int:
        async def work(c: Client) -> int:
            m = await c.send_message(self.channel_id, text)
            return int(m.id)

        return await self.pool.execute(work)

    async def _send_text_primary(self, text: str) -> int:
        async def work(c: Client) -> int:
            m = await c.send_message(self.channel_id, text)
            return int(m.id)

        return await self.pool.execute_primary(work)

    async def _edit_text(self, message_id: int, text: str) -> None:
        async def work(c: Client) -> None:
            await c.edit_message_text(self.channel_id, int(message_id), text)

        await self.pool.execute_primary(work)

    async def _get_text(self, message_id: int) -> str:
        async def work(c: Client) -> str:
            m = await c.get_messages(self.channel_id, int(message_id))
            if not m or m.empty or not m.text:
                raise ValueError("missing message text")
            return str(m.text)

        return await self.pool.execute(work)

    async def read_root(self) -> dict[str, Any]:
        raw = await self._get_text(self.root_message_id)
        return loads_safe(raw)

    async def write_root(self, root: dict[str, Any]) -> None:
        text = dumps_canonical(root)
        if len(text.encode("utf-8")) > MAX_SAFE_MESSAGE_BYTES:
            raise ValueError("root too large")
        await self._edit_text(self.root_message_id, text)

    async def ensure_root_initialized(self, *, compaction_every: int) -> dict[str, Any]:
        try:
            root = await self.read_root()
            if isinstance(root, dict) and int(root.get("v") or 0) == 2:
                return root
        except Exception:
            pass

        root = {"v": 2, "tables": {}, "compaction_every": int(compaction_every)}
        await self.write_root(root)
        return root

    async def ensure_table(self, *, table: str, schema: list[str], compaction_every: int) -> dict[str, Any]:
        async with self._root_lock:
            root = await self.ensure_root_initialized(compaction_every=compaction_every)
            tables = root.setdefault("tables", {})
            if table in tables and isinstance(tables[table], dict) and tables[table].get("root"):
                return root

            master = {"v": 2, "type": "master", "table": table, "seq": 0, "rows": {}}
            master_pages = await self._send_paged_json(master, parent_id=f"MASTER:{table}:0")
            table_root = {
                "v": 2,
                "type": "table_root",
                "table": table,
                "schema": list(schema),
                "master_pages": master_pages,
                "master_seq": 0,
                "delta_tail": None,
                "delta_seq": 0,
                "delta_count": 0,
                "compaction_every": int(compaction_every),
            }
            table_root_id = await self._send_text_primary(dumps_canonical(table_root))
            tables[table] = {"root": table_root_id}
            await self.write_root(root)
            return root

    async def _send_paged_json(self, obj: dict[str, Any], *, parent_id: str) -> list[int]:
        text = dumps_canonical(obj)
        overhead = len(encode_page(current=1, total=1, parent_id=parent_id, payload="").encode("utf-8"))
        max_payload = max(256, MAX_SAFE_MESSAGE_BYTES - overhead)
        pages = _split_text_pages(text=text, parent_id=parent_id, max_bytes=max_payload)
        mids: list[int] = []
        for p in pages:
            mids.append(await self._send_text(p))
        return mids

    async def _read_paged_json(self, message_ids: list[int]) -> dict[str, Any]:
        if not message_ids:
            raise ValueError("missing page ids")

        texts = await self._fetch_texts(message_ids)
        pages = [decode_page(t) for t in texts]
        pages.sort(key=lambda p: p.current)
        if pages[0].current != 1 or pages[-1].current != pages[0].total:
            raise ValueError("incomplete page set")
        parent = pages[0].parent_id
        if any(p.parent_id != parent for p in pages):
            raise ValueError("page parent mismatch")
        body = "".join(p.payload for p in pages)
        obj = loads_safe(body)
        if not isinstance(obj, dict):
            raise ValueError("paged json must be dict")
        return obj

    async def _fetch_texts(self, message_ids: list[int]) -> list[str]:
        async def work(c: Client) -> list[str]:
            out: list[str] = []
            for mid in message_ids:
                m = await c.get_messages(self.channel_id, int(mid))
                if not m or m.empty or not m.text:
                    raise ValueError("missing page message")
                out.append(str(m.text))
            return out

        return await self.pool.execute(work)

    async def _read_table_root(self, table_root_id: int) -> dict[str, Any]:
        raw = await self._get_text(table_root_id)
        obj = loads_safe(raw)
        if not isinstance(obj, dict) or int(obj.get("v") or 0) != 2:
            raise ValueError("invalid table root")
        return obj

    async def _write_table_root(self, table_root_id: int, obj: dict[str, Any]) -> None:
        text = dumps_canonical(obj)
        if len(text.encode("utf-8")) > MAX_SAFE_MESSAGE_BYTES:
            raise ValueError("table root too large")
        await self._edit_text(table_root_id, text)

    async def load_table_index(self, *, table: str) -> tuple[int, dict[str, Any], dict[str, Any]]:
        root = await self.read_root()
        info = (root.get("tables") or {}).get(table)
        if not isinstance(info, dict) or not info.get("root"):
            raise ValueError("unknown table")
        table_root_id = int(info["root"])
        tr = await self._read_table_root(table_root_id)
        master_pages = list(tr.get("master_pages") or [])
        master = await self._read_paged_json([int(x) for x in master_pages])

        tail = tr.get("delta_tail")
        master_seq = int(tr.get("master_seq") or 0)
        deltas: list[dict[str, Any]] = []
        cur = int(tail) if tail else 0
        while cur:
            raw = await self._get_text(cur)
            d = loads_safe(raw)
            if not isinstance(d, dict) or d.get("type") != "delta":
                break
            seq = int(d.get("seq") or 0)
            if seq <= master_seq:
                break
            deltas.append(d)
            prev = d.get("prev")
            cur = int(prev) if prev else 0
        deltas.reverse()

        idx = dict(master)
        for d in deltas:
            for op in d.get("ops") or []:
                if not isinstance(op, dict):
                    continue
                act = op.get("action")
                if act == "upsert":
                    uuid = op.get("uuid")
                    if isinstance(uuid, str):
                        idx.setdefault("rows", {})[uuid] = {
                            "pages": op.get("pages") or [],
                            "sha256": op.get("sha256"),
                        }
                elif act == "delete":
                    uuid = op.get("uuid")
                    if isinstance(uuid, str):
                        rows = idx.get("rows") or {}
                        if isinstance(rows, dict) and uuid in rows:
                            del rows[uuid]

        return table_root_id, tr, idx

    async def hydrate_all_rows(self) -> list[dict[str, Any]]:
        root = await self.read_root()
        tables = root.get("tables") or {}
        if not isinstance(tables, dict):
            return []

        out: list[dict[str, Any]] = []
        for table in list(tables.keys()):
            try:
                _table_root_id, tr, idx = await self.load_table_index(table=table)
            except Exception:
                continue
            rows = idx.get("rows") or {}
            if not isinstance(rows, dict):
                continue
            for uuid, meta in rows.items():
                if not isinstance(uuid, str) or not isinstance(meta, dict):
                    continue
                page_ids = meta.get("pages") or []
                if not isinstance(page_ids, list) or not page_ids:
                    continue
                try:
                    row_obj = await self._read_paged_json([int(x) for x in page_ids])
                except Exception:
                    continue
                if not isinstance(row_obj, dict):
                    continue
                sha = meta.get("sha256")
                if isinstance(sha, str):
                    row_text = dumps_canonical(row_obj)
                    if _sha256_hex(row_text) != sha:
                        continue
                out.append(row_obj)
        return out

    async def list_table_schemas(self) -> dict[str, list[str]]:
        root = await self.read_root()
        tables = root.get("tables") or {}
        if not isinstance(tables, dict):
            return {}
        out: dict[str, list[str]] = {}
        for table, info in tables.items():
            if not isinstance(table, str) or not isinstance(info, dict) or not info.get("root"):
                continue
            try:
                tr = await self._read_table_root(int(info["root"]))
            except Exception:
                continue
            sch = tr.get("schema") or []
            if isinstance(sch, list):
                out[table] = [str(x) for x in sch]
        return out

    async def apply_batch(  # noqa: PLR0915
        self,
        ops: list[dict[str, Any]],
        *,
        table: str,
        patch=None,  # noqa: ANN001
    ) -> None:
        root = await self.read_root()
        compaction_every = int(root.get("compaction_every") or 50)

        for op in ops:
            if op.get("kind") == "table_drop":
                async with self._root_lock:
                    root = await self.read_root()
                    tables = root.get("tables") or {}
                    if isinstance(tables, dict) and table in tables:
                        info = tables.get(table) or {}
                        if isinstance(info, dict) and info.get("root"):
                            try:
                                await self._delete_messages([int(info["root"])])
                            except Exception:
                                pass
                        del tables[table]
                        root["tables"] = tables
                        await self.write_root(root)
                return

        schema_hint: list[str] = []
        for op in ops:
            if op.get("kind") == "table_create" and isinstance(op.get("schema"), list):
                schema_hint = [str(x) for x in (op.get("schema") or [])]
                break

        await self.ensure_table(table=table, schema=schema_hint, compaction_every=compaction_every)

        table_root_id, tr, idx = await self.load_table_index(table=table)
        schema = tr.get("schema") or []
        if not schema and schema_hint:
            tr["schema"] = list(schema_hint)

        rows = idx.setdefault("rows", {})
        if not isinstance(rows, dict):
            rows = {}
            idx["rows"] = rows

        delta_ops: list[dict[str, Any]] = []
        to_delete_pages: list[int] = []

        for op in ops:
            kind = op.get("kind")
            if kind == "table_create":
                if op.get("schema"):
                    tr["schema"] = list(op["schema"])
                continue
            if kind == "row_upsert":
                uuid = str(op.get("row_uuid") or "")
                row = op.get("row")
                if not uuid or not isinstance(row, dict):
                    continue
                row_text = dumps_canonical(row)
                sha = _sha256_hex(row_text)
                existing_pages_override = op.get("tg_pages")
                mids: list[int] = []
                existing = rows.get(uuid) if isinstance(rows, dict) else None
                if isinstance(existing, dict):
                    if existing.get("sha256") == sha and existing.get("pages"):
                        continue
                if isinstance(existing_pages_override, list) and existing_pages_override:
                    try:
                        mids = [int(x) for x in existing_pages_override]
                    except Exception:
                        mids = []
                if not mids:
                    if isinstance(existing, dict):
                        for mid in existing.get("pages") or []:
                            try:
                                to_delete_pages.append(int(mid))
                            except Exception:
                                continue
                    mids = await self._send_paged_json(loads_safe(row_text), parent_id=f"ROW:{table}:{uuid}:{op.get('op_id') or ''}")
                    op_id = op.get("op_id")
                    if patch and isinstance(op_id, str):
                        await patch(op_id, {"tg_pages": mids})
                rows[uuid] = {"pages": mids, "sha256": sha}
                delta_ops.append({"action": "upsert", "uuid": uuid, "pages": mids, "sha256": sha})
                continue
            if kind == "row_delete":
                uuid = str(op.get("row_uuid") or "")
                if not uuid:
                    continue
                existing = rows.get(uuid) if isinstance(rows, dict) else None
                if isinstance(existing, dict):
                    for mid in existing.get("pages") or []:
                        try:
                            to_delete_pages.append(int(mid))
                        except Exception:
                            continue
                    del rows[uuid]
                    delta_ops.append({"action": "delete", "uuid": uuid})
                continue

        if not delta_ops:
            await self._write_table_root(table_root_id, tr)
            return

        prev_tail = tr.get("delta_tail")
        prev_tail = int(prev_tail) if prev_tail else None
        next_seq = int(tr.get("delta_seq") or 0) + 1
        delta = {
            "v": 2,
            "type": "delta",
            "table": table,
            "seq": next_seq,
            "prev": prev_tail,
            "ts_ms": int(time.time() * 1000),
            "ops": delta_ops,
        }
        existing_delta_mid = None
        if ops and isinstance(ops[0], dict) and ops[0].get("delta_mid") is not None:
            try:
                existing_delta_mid = int(ops[0].get("delta_mid"))
            except Exception:
                existing_delta_mid = None
        if existing_delta_mid:
            delta_mid = existing_delta_mid
        else:
            delta_mid = await self._send_text(dumps_canonical(delta))
            if patch:
                for op in ops:
                    op_id = op.get("op_id")
                    if isinstance(op_id, str):
                        await patch(op_id, {"delta_mid": delta_mid})

        tr["delta_tail"] = delta_mid
        tr["delta_seq"] = next_seq
        tr["delta_count"] = int(tr.get("delta_count") or 0) + 1

        if int(tr.get("delta_count") or 0) >= int(tr.get("compaction_every") or compaction_every):
            new_master_seq = next_seq
            master = {"v": 2, "type": "master", "table": table, "seq": new_master_seq, "rows": rows}
            master_pages = await self._send_paged_json(master, parent_id=f"MASTER:{table}:{new_master_seq}")
            tr["master_pages"] = master_pages
            tr["master_seq"] = new_master_seq
            tr["delta_count"] = 0

        await self._write_table_root(table_root_id, tr)

        if to_delete_pages:
            await self._delete_messages(to_delete_pages)

    async def _delete_messages(self, message_ids: list[int]) -> None:
        async def work(c: Client) -> None:
            for mid in message_ids:
                try:
                    await c.delete_messages(self.channel_id, int(mid), revoke=True)
                except Exception:
                    continue

        await self.pool.execute(work)
