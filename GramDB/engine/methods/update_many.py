"""
Multi-record update implementation for :class:`GramDB.engine.query.EfficientDictQuery`.
"""

import asyncio


async def update_many(self, table: str, query: dict, update_fields: dict) -> int:
    """
    Update all records matching ``query`` using MongoDB-style update operators.

    Parameters
    ----------
    table:
        Table name.
    query:
        Query filter. Supports the same operators as :meth:`_match_query`.
    update_fields:
        Update operators.

    Returns
    -------
    int
        Number of updated rows.
    """
    if table not in self.data:
        raise ValueError(f"Table '{table}' does not exist.")

    record_ids: list[str] = []
    for rid, rec in self.data[table].items():
        if self._match_query(rec, query):
            record_ids.append(rid)

    if not record_ids:
        raise ValueError(f"No records found matching query: {query}")

    for i, record_id in enumerate(record_ids):
        old_record = self.data[table][record_id]
        new_record = self._apply_update_operators(old_record, update_fields)
        await self._validate_record(table, new_record)

        await self._update_index_for_record(table, old_record, record_id, operation="remove")
        self.data[table][record_id] = new_record
        await self._update_index_for_record(table, new_record, record_id, operation="add")

        if i and i % 200 == 0:
            await asyncio.sleep(0)

    return len(record_ids)
