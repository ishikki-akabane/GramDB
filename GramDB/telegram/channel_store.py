from __future__ import annotations

import asyncio
import logging
from io import BytesIO
from typing import Any

from GramDB.utils.pyrogram_logging import configure_pyrogram_logging

configure_pyrogram_logging()

from pyrogram import Client
from pyrogram.types import Message

from GramDB.telegram.pyrogram_pool import PyrogramWorkerPool
from GramDB.utils.json_codec import dumps_compact, loads_safe
from GramDB.utils.retry import run_with_flood_wait_retry
from GramDB.utils.telegram_payload import (
    MAX_SAFE_MESSAGE_BYTES,
    parse_row_message,
    row_to_channel_payload,
    wrap_document_body,
)

logger = logging.getLogger("GramDB")


def _chunks(items: list[int], size: int) -> list[list[int]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


class TelegramChannelStore:
    """Low-level Telegram channel persistence for GramDB rows and the index message."""

    def __init__(
        self,
        pool: PyrogramWorkerPool,
        channel_id: int,
        index_message_id: int | None,
    ) -> None:
        self.pool = pool
        self.channel_id = channel_id
        self.index_message_id = index_message_id
        self._index_lock = asyncio.Lock()

    @staticmethod
    def empty_index() -> dict[str, Any]:
        return {"v": 1, "info": {}, "tables": {}}

    async def send_index(self, index: dict[str, Any]) -> int:
        text = dumps_compact(index)
        if len(text.encode("utf-8")) > MAX_SAFE_MESSAGE_BYTES:
            raise ValueError("index JSON exceeds safe Telegram size; reduce table row count")

        async def work(c: Client) -> int:
            m = await c.send_message(self.channel_id, text)
            return int(m.id)

        return await self.pool.execute(work)

    async def read_index_dict(self) -> dict[str, Any]:
        if self.index_message_id is None:
            raise ValueError("index_message_id is not set")

        async def work(c: Client) -> dict[str, Any]:
            msg = await c.get_messages(self.channel_id, self.index_message_id)
            if not msg or msg.empty:
                raise ValueError("index message missing or empty")
            if msg.text:
                return loads_safe(msg.text)
            raise ValueError("index message must be plain text JSON")

        return await self.pool.execute(work)

    async def write_index_dict(self, index: dict[str, Any]) -> None:
        text = dumps_compact(index)
        if len(text.encode("utf-8")) > MAX_SAFE_MESSAGE_BYTES:
            raise ValueError(
                "index JSON exceeds safe Telegram size; split data across databases or "
                "archive old rows."
            )
        mid = self.index_message_id
        if mid is None:
            raise ValueError("index_message_id is not set")

        async def work(c: Client) -> None:
            await c.edit_message_text(self.channel_id, mid, text)

        async with self._index_lock:
            await self.pool.execute(work)

    async def fetch_messages(self, message_ids: list[int]) -> list[Message]:
        if not message_ids:
            return []

        out: list[Message] = []

        async def work(c: Client) -> list[Message]:
            chunk_out: list[Message] = []
            for chunk in _chunks(message_ids, 90):
                msgs = await c.get_messages(self.channel_id, chunk)
                if isinstance(msgs, list):
                    chunk_out.extend(msgs)
                elif msgs:
                    chunk_out.append(msgs)
            return chunk_out

        # get_messages is best-effort single client for ordering
        out = await self.pool.execute(work)
        return out

    async def parse_row_message(self, message: Message) -> dict[str, Any]:
        async def work(c: Client) -> dict[str, Any]:
            if message.text:
                return parse_row_message(text=message.text, document_bytes=None)
            if message.document:
                bio = await c.download_media(message, in_memory=True)
                if bio is None:
                    raise ValueError("failed to download row document")
                data = bio.getvalue()
                return parse_row_message(text=None, document_bytes=data)
            raise ValueError("unsupported row message type (need text or document)")

        return await self.pool.execute(work)

    async def send_row(self, row: dict[str, Any]) -> int:
        text, doc = row_to_channel_payload(row)

        async def work(c: Client) -> int:
            if text is not None:
                m = await c.send_message(self.channel_id, text)
            else:
                assert doc is not None
                m = await c.send_document(
                    self.channel_id,
                    document=BytesIO(wrap_document_body(doc)),
                    file_name="gramdb_row.json",
                )
            return int(m.id)

        return await self.pool.execute(work)

    async def edit_row(self, message_id: int, row: dict[str, Any]) -> int:
        """
        Returns the effective message id (unchanged for in-place edits).
        If the new body must move to a document or grows past limits, the old
        message is deleted and a new one is sent (new id).
        """
        text, doc = row_to_channel_payload(row)

        async def work(c: Client) -> int:
            try:
                if text is not None:
                    await c.edit_message_text(self.channel_id, message_id, text)
                    return message_id
            except Exception:  # noqa: BLE001
                logger.debug("edit_message_text failed, will replace message", exc_info=True)
            try:
                await c.delete_messages(self.channel_id, message_id, revoke=True)
            except Exception:  # noqa: BLE001
                logger.debug("delete_messages failed", exc_info=True)
            if text is not None:
                m = await c.send_message(self.channel_id, text)
            else:
                assert doc is not None
                m = await c.send_document(
                    self.channel_id,
                    document=BytesIO(wrap_document_body(doc)),
                    file_name="gramdb_row.json",
                )
            return int(m.id)

        async def once() -> int:
            return await self.pool.execute(work)

        return await run_with_flood_wait_retry(once)

    async def delete_row_message(self, message_id: int) -> None:
        async def work(c: Client) -> None:
            await c.delete_messages(self.channel_id, message_id, revoke=True)

        await self.pool.execute(work)
