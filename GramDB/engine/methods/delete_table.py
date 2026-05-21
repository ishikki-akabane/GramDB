"""
Table delete implementation for :class:`GramDB.engine.query.EfficientDictQuery`.
"""

import asyncio


async def delete_table(self, table: str) -> None:
    """
    Delete an entire table and its schema.

    Parameters
    ----------
    table:
        Table name.
    """
    if table not in self.data:
        raise ValueError(f"Table '{table}' does not exist.")

    for i, (record_id, record) in enumerate(list(self.data[table].items())):
        await self._update_index_for_record(table, record, record_id, operation="remove")
        if i and i % 200 == 0:
            await asyncio.sleep(0)

    del self.data[table]
    if table in self.schemas:
        del self.schemas[table]
