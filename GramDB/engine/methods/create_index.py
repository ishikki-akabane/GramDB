"""
Single-field index build for :class:`GramDB.engine.query.EfficientDictQuery`.
"""

from collections import defaultdict


def create_index(self, field: str) -> None:
    """
    Create an index for one flattened field across all tables.

    Parameters
    ----------
    field:
        Flattened field path (for example, ``"profile.name"``).
    """
    index = defaultdict(list)
    for table_name, table in self.data.items():
        for key, item in table.items():
            flattened_item = self._flatten_dict(item)
            if field in flattened_item:
                index[flattened_item[field]].append((table_name, key))
    self.indexes[field] = index
