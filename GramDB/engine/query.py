"""
GramDB in-memory query engine.

This module defines :class:`EfficientDictQuery`, an in-memory table store used by
the public :class:`GramDB.client.GramDB` API. To keep this file small, most
public CRUD methods are implemented in separate modules under
``GramDB.engine.methods`` and attached to the class at
import time.
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import random
import string


class EfficientDictQuery:
    """
    Dictionary-backed query engine.

    Data Model
    ----------
    data:
        ``self.data[table_name][record_id] -> record``
    schemas:
        ``self.schemas[table_name] -> tuple[field, ...]``
    indexes:
        ``self.indexes[field_name][field_value] -> list[(table_name, record_id)]``
    """

    def __init__(self, data: dict):
        """
        Initialize the engine with a hydrated GramDB dataset.

        Parameters
        ----------
        data:
            Mapping of ``_m_id`` to Telegram-backed rows. Each row must include
            ``_table_`` and ``_id``.
        """
        self.data = self._structure_data(data)
        self.indexes = defaultdict(lambda: defaultdict(list))
        self.schemas: dict[str, tuple[str, ...]] = {}
        self.create_all_indexes()
        self.create_all_schemas()

    def _structure_data(self, data: dict) -> defaultdict:
        """
        Convert hydrated rows into a table-oriented structure.

        The hydrated shape is ``{_m_id: row}``. The internal shape becomes:
        ``{table_name: {record_id: row_without__table_}}``.
        """
        structured_data: defaultdict[str, dict] = defaultdict(dict)
        for record in data.values():
            table = record["_table_"]
            primary_key = record["_id"]
            structured_record = {k: v for k, v in record.items() if k != "_table_"}
            structured_data[table][str(primary_key)] = structured_record
        return structured_data

    def _flatten_dict(self, d: dict, parent_key: str = "", sep: str = ".") -> dict:
        """
        Flatten nested dict/list structures into dot-path keys.

        Examples
        --------
        ``{"a": {"b": 1}}`` becomes ``{"a.b": 1}``.
        ``{"tags": ["x", "y"]}`` becomes ``{"tags.0": "x", "tags.1": "y"}``.
        """
        items: list[tuple[str, object]] = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else str(k)
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    items.extend(self._flatten_dict({str(i): item}, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _apply_update_operators(self, record: dict, update_fields: dict) -> dict:
        """
        Apply MongoDB-style update operators.

        Supported Operators
        -------------------
        $set, $unset, $inc, $mul, $push, $pull, $addToSet, $rename

        Notes
        -----
        This method operates on a deep copy of the input record to avoid mutating
        the original during update planning.
        """
        new_record = deepcopy(record)
        for operator, updates in update_fields.items():
            if operator == "$set":
                new_record.update(updates)

            elif operator == "$unset":
                if isinstance(updates, dict):
                    for key in updates:
                        new_record.pop(key, None)
                elif isinstance(updates, (list, tuple)):
                    for key in updates:
                        new_record.pop(key, None)
                else:
                    new_record.pop(updates, None)

            elif operator == "$inc":
                for key, value in updates.items():
                    if key in new_record and isinstance(new_record[key], (int, float)):
                        new_record[key] += value
                    else:
                        raise ValueError(f"Cannot increment non-numeric field '{key}'")

            elif operator == "$mul":
                for key, value in updates.items():
                    if key in new_record and isinstance(new_record[key], (int, float)):
                        new_record[key] *= value
                    else:
                        raise ValueError(f"Cannot increment non-numeric field '{key}'")

            elif operator == "$push":
                for key, value in updates.items():
                    if key in new_record and isinstance(new_record[key], list):
                        new_record[key].append(value)
                    else:
                        raise ValueError(f"Cannot push to non-list field '{key}'")

            elif operator == "$pull":
                for key, value in updates.items():
                    if key in new_record and isinstance(new_record[key], list):
                        new_record[key] = [item for item in new_record[key] if item != value]
                    else:
                        raise ValueError(f"Cannot pull from non-list field '{key}'")

            elif operator == "$addToSet":
                for key, value in updates.items():
                    if key in new_record and isinstance(new_record[key], list):
                        if value not in new_record[key]:
                            new_record[key].append(value)
                        else:
                            raise ValueError(f"unable to push value already existed '{key}'")
                    else:
                        raise ValueError(f"Cannot push to non-list field '{key}'")
                        
            elif operator == "$rename":
                for key, value in updates.items():
                    if key in new_record:
                        new_record[value] = new_record.pop(f"{key}")
                    else:
                        raise ValueError(f"Key doesn't exists {key}")
            else:
                raise ValueError(f"Unknown update operator: '{operator}'")
        return new_record
    
    def _match_query(self, record: dict, query: dict) -> bool:
        """
        Check whether a record matches a query filter.

        Supported Query Operators
        -------------------------
        Logical: ``$or``, ``$and``, ``$nor``
        Comparisons: ``$gt``, ``$gte``, ``$lt``, ``$lte``, ``$ne``, ``$in``, ``$nin``
        """
        for key, value in query.items():
            if key == "$or":
                if not any(self._match_query(record, q) for q in value):
                    return False
                continue

            if key == "$and":
                if not all(self._match_query(record, q) for q in value):
                    return False
                continue

            if key == "$nor":
                if any(self._match_query(record, q) for q in value):
                    return False
                continue
            record_value = record.get(key)

            if isinstance(value, dict):
                for op, cond in value.items():

                    if op == "$gt" and not (record_value > cond):
                        return False
                    if op == "$gte" and not (record_value >= cond):
                        return False
                    if op == "$lt" and not (record_value < cond):
                        return False
                    if op == "$lte" and not (record_value <= cond):
                        return False
                    if op == "$ne" and not (record_value != cond):
                        return False
                    if op == "$in" and not (record_value in cond):
                        return False
                    if op == "$nin" and (record_value in cond):
                        return False

            else:
                if record_value != value:
                    return False

        return True
    
    async def _update_index_for_record(self, table, record, record_id, operation='add'):
        """
        Update indexes after a record insertion, update, or delete.

        Parameters
        ----------
        table:
            Table name.
        record:
            Record payload (unflattened).
        record_id:
            Record primary key.
        operation:
            ``"add"`` or ``"remove"``.
        """
        flattened_record = self._flatten_dict(record)
        for field, value in flattened_record.items():
            if operation == 'add':
                self.indexes[field][value].append((table, record_id))
            elif operation == 'remove':
                if (table, record_id) in self.indexes[field][value]:
                    self.indexes[field][value].remove((table, record_id))
                    if not self.indexes[field][value]:
                        del self.indexes[field][value]

    async def _validate_record(self, table: str, record: dict) -> None:
        """
        Validate a record against the table schema.

        A record must contain all schema fields and must not introduce unknown
        fields.
        """
        if table not in self.schemas:
            raise ValueError(f"Table '{table}' does not exist.")

        schema = self.schemas[table]
        for field in schema:
            if field not in record:
                raise ValueError(f"Missing required field '{field}' in record for table '{table}'.")
                
        for field in record:
            if field not in schema:
                raise ValueError(f"Field '{field}' is not allowed in schema for table '{table}'.")

    async def _generate_random_id(self):
        """
        Generates a random ID.

        :return: A random 20-character ID.
        """
        return ''.join(random.choices(string.ascii_letters + string.digits, k=20))

    async def old_update(self, *args, **kwargs):
        """
        Backwards-compatibility stub for older GramDB update APIs.

        Use :meth:`update_one` with update operators such as ``{"$set": {...}}``.
        """
        raise NotImplementedError("old_update() removed — use update_one() with {'$set': {...}}")


from .methods.check_table import check_table as _check_table
from .methods.create import create as _create
from .methods.create_all_indexes import create_all_indexes as _create_all_indexes
from .methods.create_all_schemas import create_all_schemas as _create_all_schemas
from .methods.create_index import create_index as _create_index
from .methods.delete_many import delete_many as _delete_many
from .methods.delete_one import delete_one as _delete_one
from .methods.delete_table import delete_table as _delete_table
from .methods.fetch import fetch as _fetch
from .methods.fetch_all import fetch_all as _fetch_all
from .methods.insert_many import insert_many as _insert_many
from .methods.insert_one import insert_one as _insert_one
from .methods.update_many import update_many as _update_many
from .methods.update_one import update_one as _update_one

EfficientDictQuery.check_table = _check_table
EfficientDictQuery.create = _create
EfficientDictQuery.create_all_indexes = _create_all_indexes
EfficientDictQuery.create_all_schemas = _create_all_schemas
EfficientDictQuery.create_index = _create_index
EfficientDictQuery.delete_many = _delete_many
EfficientDictQuery.delete_one = _delete_one
EfficientDictQuery.delete_table = _delete_table
EfficientDictQuery.fetch = _fetch
EfficientDictQuery.fetch_all = _fetch_all
EfficientDictQuery.insert_many = _insert_many
EfficientDictQuery.insert_one = _insert_one
EfficientDictQuery.update_many = _update_many
EfficientDictQuery.update_one = _update_one

