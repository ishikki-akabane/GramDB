from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable

from GramDB.exception import GramDBError
from GramDB.persistence.ops import SyncOp
from GramDB.persistence.wal import WriteAheadLog


ApplyBatchFn = Callable[[list[SyncOp]], Awaitable[None]]


class WriteFrozenError(GramDBError):
    pass


class PersistenceManager:
    def __init__(
        self,
        *,
        wal: WriteAheadLog,
        apply_batch: ApplyBatchFn,
        batch_window_ms: int = 200,
        max_concurrent_tables: int = 4,
    ) -> None:
        self._wal = wal
        self._apply_batch = apply_batch
        self._batch_window_ms = int(batch_window_ms)
        self._max_concurrent_tables = int(max_concurrent_tables)

        self._table_queues: dict[str, asyncio.Queue[SyncOp]] = {}
        self._table_tasks: dict[str, asyncio.Task[None]] = {}
        self._dispatcher_task: asyncio.Task[None] | None = None
        self._incoming: asyncio.Queue[SyncOp] = asyncio.Queue()

        self._started = False
        self._stop_evt = asyncio.Event()
        self._can_run = asyncio.Event()
        self._can_run.set()
        self._idle_evt = asyncio.Event()
        self._idle_evt.set()
        self._state_lock = asyncio.Lock()
        self._in_flight = 0

        self._frozen = False
        self._frozen_reason: str | None = None

        self._sem = asyncio.Semaphore(self._max_concurrent_tables)

    @property
    def frozen(self) -> bool:
        return self._frozen

    @property
    def frozen_reason(self) -> str | None:
        return self._frozen_reason

    def freeze(self, reason: str) -> None:
        self._frozen = True
        self._frozen_reason = reason
        self._can_run.clear()

    def unfreeze(self) -> None:
        self._frozen = False
        self._frozen_reason = None
        self._can_run.set()

    async def _mark_activity(self) -> None:
        async with self._state_lock:
            self._idle_evt.clear()

    async def _maybe_mark_idle(self) -> None:
        async with self._state_lock:
            if self._in_flight != 0:
                return
            if not self._incoming.empty():
                return
            if any(not q.empty() for q in self._table_queues.values()):
                return
            self._idle_evt.set()

    async def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._stop_evt.clear()
        self._dispatcher_task = asyncio.create_task(self._dispatcher_loop(), name="gramdb-dispatcher")

    async def stop(self) -> None:
        if not self._started:
            return
        self._stop_evt.set()
        if self._dispatcher_task:
            self._dispatcher_task.cancel()
            try:
                await self._dispatcher_task
            except asyncio.CancelledError:
                pass
            self._dispatcher_task = None

        for t in list(self._table_tasks.values()):
            t.cancel()
        for k, t in list(self._table_tasks.items()):
            try:
                await t
            except asyncio.CancelledError:
                pass
            self._table_tasks.pop(k, None)
        self._table_queues.clear()
        self._started = False
        self._idle_evt.set()

    async def enqueue(self, op: SyncOp) -> None:
        if self._frozen:
            raise WriteFrozenError(self._frozen_reason or "writes are frozen")
        await self._wal.append_op(op)
        await self._mark_activity()
        await self._incoming.put(op)

    async def recover_from_wal(self) -> int:
        pending = await self._wal.load_pending()
        if pending:
            await self._mark_activity()
        for op in pending:
            await self._incoming.put(op)
        return len(pending)

    async def flush(self) -> None:
        await self._maybe_mark_idle()
        await self._idle_evt.wait()

    async def _dispatcher_loop(self) -> None:
        try:
            while not self._stop_evt.is_set():
                op = await self._incoming.get()
                await self._mark_activity()
                q = self._table_queues.get(op.table)
                if q is None:
                    q = asyncio.Queue()
                    self._table_queues[op.table] = q
                    self._table_tasks[op.table] = asyncio.create_task(
                        self._table_worker(op.table, q),
                        name=f"gramdb-table-worker:{op.table}",
                    )
                await q.put(op)
                await self._maybe_mark_idle()
        except asyncio.CancelledError:
            return

    async def _table_worker(self, table: str, q: asyncio.Queue[SyncOp]) -> None:
        async with self._sem:
            try:
                carry: SyncOp | None = None
                while not self._stop_evt.is_set():
                    await self._can_run.wait()
                    if carry is not None:
                        op = carry
                        carry = None
                    else:
                        op = await q.get()
                    batch = [op]

                    if op.kind != "table_drop":
                        t_deadline = time.perf_counter() + (self._batch_window_ms / 1000.0)
                        while True:
                            remaining = t_deadline - time.perf_counter()
                            if remaining <= 0:
                                break
                            try:
                                nxt = await asyncio.wait_for(q.get(), timeout=remaining)
                            except asyncio.TimeoutError:
                                break
                            if nxt.kind == "table_drop":
                                carry = nxt
                                break
                            batch.append(nxt)

                    while True:
                        try:
                            async with self._state_lock:
                                self._in_flight += 1
                                self._idle_evt.clear()
                            await self._apply_batch(batch)
                            for b in batch:
                                await self._wal.ack(b.op_id, "done")
                            break
                        except Exception as e:  # noqa: BLE001
                            name = type(e).__name__
                            msg = str(e)
                            if "403" in msg or "401" in msg or "Forbidden" in msg or "Unauthorized" in msg:
                                self.freeze(f"panic: telegram auth failure ({name})")
                                await self._can_run.wait()
                                continue
                            await asyncio.sleep(0.5)
                        finally:
                            async with self._state_lock:
                                self._in_flight = max(0, self._in_flight - 1)
                            await self._maybe_mark_idle()
            except asyncio.CancelledError:
                return
