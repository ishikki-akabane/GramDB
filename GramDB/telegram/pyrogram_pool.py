from __future__ import annotations

import asyncio
import hashlib
import logging
import tempfile
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

from GramDB.utils.pyrogram_logging import configure_pyrogram_logging

configure_pyrogram_logging()

from pyrogram import Client
from pyrogram.enums import ChatMemberStatus

from GramDB.exception import GramDBTelegramError

logger = logging.getLogger("GramDB")

T = TypeVar("T")


def _token_fp(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:10]


class PyrogramWorkerPool:
    """
    One Pyrogram bot client per token. ``execute`` picks workers in round-robin
    order so load spreads across tokens (flood-limit friendly).
    """

    def __init__(self, bot_tokens: list[str], api_id: int, api_hash: str) -> None:
        if not bot_tokens:
            raise ValueError("Provide at least one bot token (two or more are recommended).")
        
        self._api_id = api_id
        self._api_hash = api_hash
        self._tokens = list(dict.fromkeys(bot_tokens))
        self._clients: list[Client] = []
        self._cooldown_until: list[float] = []
        self._rr = 0
        self._lock = asyncio.Lock()
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        async with self._lock:
            if self._started:
                return
            for i, token in enumerate(self._tokens):
                session = f"gramdb_{i}_{_token_fp(token)}"
                # workdir = tempfile.mkdtemp(prefix="gramdb_session_")
                client = Client(
                    session,
                    bot_token=token,
                    api_id=self._api_id, api_hash=self._api_hash,
                    no_updates=True,
                    # workdir=workdir
                )
                await client.start()
                self._clients.append(client)
                self._cooldown_until.append(0.0)
                logger.info("Started Pyrogram worker %s (session dir %s)", i, session)
            self._started = True

    async def stop(self) -> None:
        for c in self._clients:
            try:
                await c.stop()
            except Exception:  # noqa: BLE001
                logger.exception("error stopping pyrogram client")
        self._clients.clear()
        self._cooldown_until.clear()
        self._started = False

    async def _pick_client(self) -> tuple[Client, int]:
        while True:
            now = time.monotonic()
            if not self._clients:
                raise RuntimeError("PyrogramWorkerPool is not started")
            n = len(self._clients)
            for _ in range(n):
                idx = self._rr % n
                self._rr += 1
                if self._cooldown_until[idx] <= now:
                    return self._clients[idx], idx
            soonest = min(self._cooldown_until) if self._cooldown_until else now + 1.0
            await asyncio.sleep(max(0.5, soonest - now))

    async def execute(self, fn: Callable[[Client], Awaitable[T]]) -> T:
        last_exc: BaseException | None = None
        for attempt in range(1, 13):
            client, idx = await self._pick_client()
            try:
                return await fn(client)
            except Exception as e:  # noqa: BLE001
                name = type(e).__name__
                if name == "FloodWait":
                    wait_s = int(getattr(e, "value", 1)) + min(attempt, 5)
                    self._cooldown_until[idx] = max(self._cooldown_until[idx], time.monotonic() + wait_s)
                    last_exc = e
                    continue
                raise
        assert last_exc is not None
        raise last_exc

    async def execute_primary(self, fn: Callable[[Client], Awaitable[T]]) -> T:
        if not self._clients:
            raise RuntimeError("PyrogramWorkerPool is not started")
        last_exc: BaseException | None = None
        idx = 0
        for attempt in range(1, 13):
            now = time.monotonic()
            wait = self._cooldown_until[idx] - now
            if wait > 0:
                await asyncio.sleep(wait)
            client = self._clients[idx]
            try:
                return await fn(client)
            except Exception as e:  # noqa: BLE001
                name = type(e).__name__
                if name == "FloodWait":
                    wait_s = int(getattr(e, "value", 1)) + min(attempt, 5)
                    self._cooldown_until[idx] = max(self._cooldown_until[idx], time.monotonic() + wait_s)
                    last_exc = e
                    continue
                raise
        assert last_exc is not None
        raise last_exc

    async def ensure_channel_admin(self, channel_id: int) -> None:
        """
        Every worker bot must be able to post in the channel. Raises if any bot
        lacks administrator privileges with posting rights.
        """

        async def check_one(client: Client) -> None:
            me = await client.get_me()
            member = await client.get_chat_member(channel_id, me.id)
            ok = False
            if member.status == ChatMemberStatus.OWNER:
                ok = True
            elif member.status == ChatMemberStatus.ADMINISTRATOR:
                priv = member.privileges
                if priv is not None and getattr(priv, "can_post_messages", False):
                    ok = True
                elif priv is not None and getattr(priv, "can_manage_chat", False):
                    ok = True
            if not ok:
                raise GramDBTelegramError(
                    f"bot @{getattr(me, 'username', None) or me.id} is not a channel admin "
                    "with can_post_messages (add every bot token as administrator)."
                )

        for c in self._clients:
            await check_one(c)
