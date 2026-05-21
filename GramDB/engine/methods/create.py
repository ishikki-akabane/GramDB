"""
Table creation implementation for :class:`GramDB.engine.query.EfficientDictQuery`.
"""


async def create(self, table: str, schema, sample_record: dict, _m_id: str) -> None:
    """
    Create a new table with a schema and one sample row.

    GramDB stores table schemas inside the in-memory engine. The first row is a
    sample row used to persist and re-hydrate the schema later.

    Parameters
    ----------
    table:
        Table name to create.
    schema:
        Iterable of allowed field names.
    sample_record:
        Sample row payload. Must contain all schema fields.
    _m_id:
        Metadata ID for the sample row.
    """
    if table in self.data or table in self.schemas:
        raise ValueError(f"Table '{table}' already exists.")

    schema_set = set(schema)
    schema_set.update(["_id", "_m_id"])
    self.schemas[table] = tuple(schema_set)

    sample = dict(sample_record)
    sample.setdefault("_id", "sample1928")
    sample["_id"] = str(sample["_id"])
    sample["_m_id"] = _m_id

    await self._validate_record(table, sample)

    self.data[table] = {str(sample["_id"]): sample}
    await self._update_index_for_record(table, sample, str(sample["_id"]), operation="add")
