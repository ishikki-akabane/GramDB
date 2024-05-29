from collections import defaultdict
import asyncio

class EfficientDictQuery:
    def __init__(self, data):
        self.data = data
        self.indexes = defaultdict(dict)
        self.create_all_indexes()

    def create_all_indexes(self):
        if not self.data:
            return

        fields = set()
        for item in self.data.values():
            flattened_item = self._flatten_dict(item)
            fields.update(flattened_item.keys())
        
        for field in fields:
            self.create_index(field)

    def create_index(self, field):
        index = defaultdict(list)
        for key, item in self.data.items():
            flattened_item = self._flatten_dict(item)
            if field in flattened_item:
                index[flattened_item[field]].append(key)
        self.indexes[field] = index

    def _flatten_dict(self, d, parent_key='', sep='.'):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    items.extend(self._flatten_dict({str(i): item}, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    
    async def fetch(self, field, value):
        if field == '_id':
            return [self.data.get(value, {})]
        
        if field not in self.indexes:
            raise ValueError(f"Index for field '{field}' does not exist. Please create it first.")
        
        keys = self.indexes[field].get(value, [])
        return [{key: self.data[key]} for key in keys]

    async def _update_index_for_record(self, record, record_id, operation='add'):
        flattened_record = self._flatten_dict(record)
        for field, value in flattened_record.items():
            if operation == 'add':
                self.indexes[field][value].append(record_id)
            elif operation == 'remove':
                if record_id in self.indexes[field][value]:
                    self.indexes[field][value].remove(record_id)
                    if not self.indexes[field][value]:
                        del self.indexes[field][value]

    async def insert(self, record):
        if '_id' not in record:
            raise ValueError("Record must contain '_id' field.")
        
        _id = record['_id']
        if _id in self.data:
            raise ValueError(f"Record with _id '{_id}' already exists.")
        
        self.data[_id] = record
        await self._update_index_for_record(record, _id, operation='add')

    async def update(self, _id, update_fields):
        if _id not in self.data:
            raise ValueError(f"Record with _id '{_id}' does not exist.")
        
        old_record = self.data[_id]
        await self._update_index_for_record(old_record, _id, operation='remove')
        
        self.data[_id].update(update_fields)
        await self._update_index_for_record(self.data[_id], _id, operation='add')

    async def delete(self, _id):
        if _id not in self.data:
            raise ValueError(f"Record with _id '{_id}' does not exist.")
        
        record = self.data[_id]
        await self._update_index_for_record(record, _id, operation='remove')
        del self.data[_id]

    async def fetch_all(self):
        return self.data

