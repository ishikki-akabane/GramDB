"""
Utilities for controlling Pyrogram logging noise.

GramDB uses Pyrogram as its Telegram transport. Pyrogram emits some warnings at
import time (for example when TgCrypto isn't installed). For an end-user library
experience, GramDB defaults to silencing Pyrogram loggers.
"""

from __future__ import annotations

import logging
import os


def configure_pyrogram_logging() -> None:
    """
    Configure Pyrogram loggers for GramDB.

    Default behavior is to silence Pyrogram logs by setting the ``pyrogram``
    logger level to ``ERROR`` and preventing propagation to the root logger.

    Users can opt out by setting ``GRAMDB_SHOW_PYROGRAM_LOGS=1``.
    """
    show = os.getenv("GRAMDB_SHOW_PYROGRAM_LOGS", "").strip().lower()
    if show in {"1", "true", "yes", "on"}:
        return

    level_name = os.getenv("GRAMDB_PYROGRAM_LOG_LEVEL", "ERROR").strip().upper()
    level = getattr(logging, level_name, logging.ERROR)

    lg = logging.getLogger("pyrogram")
    lg.setLevel(level)
    lg.propagate = False
    if not lg.handlers:
        lg.addHandler(logging.NullHandler())
