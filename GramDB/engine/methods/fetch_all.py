"""
Fetch-all implementation for :class:`GramDB.engine.query.EfficientDictQuery`.
"""


async def fetch_all(self, table: str | None = None):
    """
    Fetch all records for a table or the full in-memory dataset.

    Parameters
    ----------
    table:
        If provided, returns records for only this table.
    """
    if table is not None:
        return self.data[table]
    return self.data
