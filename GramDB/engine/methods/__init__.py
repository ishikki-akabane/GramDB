"""
Implementation helpers for :class:`GramDB.engine.query.EfficientDictQuery`.

This package keeps the public query engine class small by hosting the method
implementations in dedicated modules
"""

__all__ = [
    "check_table",
    "create",
    "create_all_indexes",
    "create_all_schemas",
    "create_index",
    "delete_many",
    "delete_one",
    "delete_table",
    "fetch",
    "fetch_all",
    "insert_many",
    "insert_one",
    "update_many",
    "update_one",
]

from .check_table import check_table
from .create import create
from .create_all_indexes import create_all_indexes
from .create_all_schemas import create_all_schemas
from .create_index import create_index
from .delete_many import delete_many
from .delete_one import delete_one
from .delete_table import delete_table
from .fetch import fetch
from .fetch_all import fetch_all
from .insert_many import insert_many
from .insert_one import insert_one
from .update_many import update_many
from .update_one import update_one
