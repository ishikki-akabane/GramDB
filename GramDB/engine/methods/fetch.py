"""
Query implementation for :class:`GramDB.engine.query.EfficientDictQuery`.
"""

import asyncio


async def fetch(self, table: str, query: dict) -> list[dict]:
    """
    Fetch records from a table that match ``query``.

    Parameters
    ----------
    table:
        Table name.
    query:
        Query filter. Supports the same operators as :meth:`_match_query`.

    Returns
    -------
    list[dict]
        Matching records.
    """
    results: list[dict] = []

    for i, (_record_id, record) in enumerate(self.data.get(table, {}).items()):
        if self._match_query(record, query):
            results.append(record)
        if i and i % 500 == 0:
            await asyncio.sleep(0)

    return results
