"""
Single-record delete implementation for :class:`GramDB.engine.query.EfficientDictQuery`.
"""


async def delete_one(self, table: str, query: dict) -> str:
    """
    Delete the first record matching ``query``.

    Parameters
    ----------
    table:
        Table name.
    query:
        Query filter. Supports the same operators as :meth:`_match_query`.

    Returns
    -------
    str
        The deleted record's ``_m_id``.
    """
    if table not in self.data:
        raise ValueError(f"Table '{table}' does not exist.")

    for record_id, record in self.data[table].items():
        if not self._match_query(record, query):
            continue

        _m_id = str(record["_m_id"])
        await self._update_index_for_record(table, record, record_id, operation="remove")
        del self.data[table][record_id]
        return _m_id

    raise ValueError(f"No records found matching query: {query}")
