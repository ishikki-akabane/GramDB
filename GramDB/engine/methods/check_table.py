"""
Table existence check for :class:`GramDB.engine.query.EfficientDictQuery`.
"""


async def check_table(self, table: str) -> bool:
    """
    Check whether a table exists (schema-based).

    Parameters
    ----------
    table:
        Table name.
    """
    return table in self.schemas
