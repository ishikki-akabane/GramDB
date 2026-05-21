"""
Index bootstrapping for :class:`GramDB.engine.query.EfficientDictQuery`.
"""


def create_all_indexes(self) -> None:
    """
    Build indexes for every field found in the current dataset.

    Index keys are the flattened field paths produced by :meth:`_flatten_dict`.
    This is automatically called during initialization.
    """
    if not self.data:
        return

    fields: set[str] = set()
    for table in self.data.values():
        for item in table.values():
            flattened_item = self._flatten_dict(item)
            fields.update(flattened_item.keys())

    for field in fields:
        self.create_index(field)
