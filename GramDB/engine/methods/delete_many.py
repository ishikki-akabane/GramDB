"""
Multi-record delete implementation for :class:`GramDB.engine.query.EfficientDictQuery`.
"""

import asyncio


async def delete_many(self, table: str, query: dict) -> int:
    """
    Delete all records matching ``query``.

    Parameters
    ----------
    table:
        Table name.
    query:
        Query filter. Supports the same operators as :meth:`_match_query`.

    Returns
    -------
    int
        Number of deleted rows.
    """
    if table not in self.data:
        raise ValueError(f"Table '{table}' does not exist.")

    record_ids: list[str] = []
    for record_id, record in self.data[table].items():
        if self._match_query(record, query):
            record_ids.append(record_id)

    if not record_ids:
        raise ValueError(f"No records found matching query: {query}")

    for i, record_id in enumerate(record_ids):
        record = self.data[table][record_id]
        await self._update_index_for_record(table, record, record_id, operation="remove")
        del self.data[table][record_id]

        if i and i % 200 == 0:
            await asyncio.sleep(0)

    return len(record_ids)
