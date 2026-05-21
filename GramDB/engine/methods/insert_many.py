"""
Multi-record insert implementation for :class:`GramDB.engine.query.EfficientDictQuery`.
"""

import asyncio


async def insert_many(self, table: str, records: list[dict], **kwargs) -> dict:
    """
    Insert multiple records into an existing table.

    Missing ``_id`` values are auto-generated. The caller must provide ``_m_id``
    as a keyword argument.

    Parameters
    ----------
    table:
        Table name.
    records:
        Records to insert.
    _m_id:
        Row UUID / metadata ID to attach to every inserted record (keyword-only).

    Returns
    -------
    dict
        ``{"inserted_ids": [...], "errors": [...]}``
    """
    _m_id = kwargs.get("_m_id")
    if not _m_id:
        raise ValueError("insert_many requires '_m_id'")

    if table not in self.data:
        raise ValueError(f"Table '{table}' does not exist.")

    inserted_ids: list[str] = []
    errors: list[dict] = []

    for i, record in enumerate(records):
        try:
            if "_id" not in record:
                record["_id"] = await self._generate_random_id()

            await self.insert_one(table, record, _m_id=_m_id)
            inserted_ids.append(str(record["_id"]))
        except Exception as e:
            errors.append({"record": record, "error": str(e)})

        if i and i % 200 == 0:
            await asyncio.sleep(0)

    return {"inserted_ids": inserted_ids, "errors": errors}
