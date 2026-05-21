"""
Schema bootstrapping for :class:`GramDB.engine.query.EfficientDictQuery`.
"""


def create_all_schemas(self) -> None:
    """
    Infer per-table schemas from existing data.

    The schema is stored as a tuple of allowed field names. This is automatically
    called during initialization.
    """
    for table_name, records in self.data.items():
        if table_name in self.schemas:
            continue
        schema: set[str] = set()
        for record in records.values():
            schema.update(record.keys())
        self.schemas[table_name] = tuple(schema)
