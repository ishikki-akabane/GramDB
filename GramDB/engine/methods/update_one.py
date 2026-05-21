"""
Single-record update implementation for :class:`GramDB.engine.query.EfficientDictQuery`.
"""


async def update_one(self, table: str, query: dict, update_fields: dict) -> tuple[str, str]:
    """
    Update one record matching ``query`` using MongoDB-style update operators.

    The first matching record is updated. Indexes are updated to reflect the new
    values.

    Parameters
    ----------
    table:
        Table name.
    query:
        Query filter. Supports the same operators as :meth:`_match_query`.
    update_fields:
        Update operators (``$set``, ``$unset``, ``$inc``, ``$mul``, ``$push``,
        ``$pull``, ``$addToSet``, ``$rename``).

    Returns
    -------
    tuple[str, str]
        ``(_m_id, _id)`` of the updated row.
    """
    if table not in self.data:
        raise ValueError(f"Table '{table}' does not exist.")

    record_id: str | None = None
    old_record: dict | None = None
    for rid, rec in self.data[table].items():
        if self._match_query(rec, query):
            record_id = rid
            old_record = rec
            break

    if record_id is None or old_record is None:
        raise ValueError(f"No records found matching query: {query}")

    _m_id = str(old_record["_m_id"])
    _id = str(old_record["_id"])

    new_record = self._apply_update_operators(old_record, update_fields)
    await self._validate_record(table, new_record)

    await self._update_index_for_record(table, old_record, record_id, operation="remove")
    self.data[table][record_id] = new_record
    await self._update_index_for_record(table, new_record, record_id, operation="add")

    return _m_id, _id
