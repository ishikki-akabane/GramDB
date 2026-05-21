"""
Single-record insert implementation for :class:`GramDB.engine.query.EfficientDictQuery`.
"""


async def insert_one(self, table: str, record: dict, **kwargs) -> None:
    """
    Insert one record into an existing table.

    The caller must provide ``_m_id`` as a keyword argument. The record must have
    ``_id`` and all fields required by the table schema.

    Parameters
    ----------
    table:
        Table name.
    record:
        Row payload to insert. The object is stored as-is after adding ``_m_id``.
    _m_id:
        Row UUID / metadata ID (keyword-only).

    Raises
    ------
    ValueError
        If the table does not exist, if ``_m_id`` is missing, if ``_id`` is
        missing, or if a record with the same ``_id`` already exists.
    """
    _m_id = kwargs.get("_m_id")
    if not _m_id:
        raise ValueError("Record must contain '_m_id' as a keyword argument.")

    if table not in self.data:
        raise ValueError(f"Invalid table name '{table}'. Table does not exist.")

    if "_id" not in record:
        raise ValueError("Record must contain '_id'.")

    _id = str(record["_id"])
    record["_id"] = _id
    record["_m_id"] = _m_id

    await self._validate_record(table, record)

    if _id in self.data[table]:
        raise ValueError(f"Record with _id '{_id}' already exists in table '{table}'.")

    self.data[table][_id] = record
    await self._update_index_for_record(table, record, _id, operation="add")
