from collections import defaultdict
import random
import string

class EfficientDictQuery:
    def __init__(self, data):
        self.data = self._structure_data(data)
        self.indexes = defaultdict(lambda: defaultdict(list))
        self.schemas = {}
        self.create_all_indexes()

    def _structure_data(self, data):
        structured_data = defaultdict(dict)
        for record in data.values():
            table = record['_table_']
            primary_key = record['_id']
            structured_record = {k: v for k, v in record.items() if k not in ['_table_']}
            structured_data[table][str(primary_key)] = structured_record
        return structured_data

    def create_all_indexes(self):
        if not self.data:
            return

        fields = set()
        for table in self.data.values():
            for item in table.values():
                flattened_item = self._flatten_dict(item)
                fields.update(flattened_item.keys())
        
        for field in fields:
            self.create_index(field)

    def create_index(self, field):
        index = defaultdict(list)
        for table_name, table in self.data.items():
            for key, item in table.items():
                flattened_item = self._flatten_dict(item)
                if field in flattened_item:
                    index[flattened_item[field]].append((table_name, key))
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

    
    async def fetch(self, table, query):
        results = []

        for record_id, record in self.data.get(table, {}).items():
            if all(record.get(key) == value for key, value in query.items()):
                results.append(record)

        return results

    async def _update_index_for_record(self, table, record, record_id, operation='add'):
        flattened_record = self._flatten_dict(record)
        for field, value in flattened_record.items():
            if operation == 'add':
                self.indexes[field][value].append((table, record_id))
            elif operation == 'remove':
                if (table, record_id) in self.indexes[field][value]:
                    self.indexes[field][value].remove((table, record_id))
                    if not self.indexes[field][value]:
                        del self.indexes[field][value]

    async def _validate_record(self, table, record):
        if table not in self.schemas:
            return True  # No schema defined, so everything is valid

        schema = self.schemas[table]
        for field in schema:
            if field not in record:
                raise ValueError(f"Missing required field '{field}' in record for table '{table}'.")

    async def create(self, table, schema):
        if table in self.data:
            raise ValueError(f"Table '{table}' already exists.")

        self.schemas[table] = schema

        sample_record = {field: "test" for field in schema}
        sample_record['_id'] = "sample1928"

        self.data[table] = {"sample1928": sample_record}
        await self._update_index_for_record(table, sample_record, "6829298293", operation='add')

    async def _generate_random_id(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                               
    async def insert(self, table, record, **kwargs):
        _m_id = kwargs.get('_m_id')
        if not _m_id:
            raise ValueError("Record must contain '_m_id' as a keyword argument.")

        if '_id' not in record:
            record['_id'] = await self._generate_random_id()
        
        _id = str(record['_id'])
        record['_m_id'] = _m_id

        await self._validate_record(table, record)

        if _id in self.data[table]:
            raise ValueError(f"Record with _id '{_id}' already exists in table '{table}'.")

        self.data[table][_id] = record
        await self._update_index_for_record(table, record, _id, operation='add')

    async def update(self, table, _id, update_fields):
        _id = str(_id)
        if _id not in self.data[table]:
            raise ValueError(f"Record with _id '{_id}' does not exist in table '{table}'.")
        
        old_record = self.data[table][_id]
        await self._update_index_for_record(table, old_record, _id, operation='remove')
        
        self.data[table][_id].update(update_fields)
        await self._update_index_for_record(table, self.data[table][_id], _id, operation='add')

    async def delete(self, table, query):
        if table not in self.data:
            raise ValueError(f"Table '{table}' does not exist.")

        records_to_delete = [
            record_id for record_id, record in self.data[table].items()
            if all(record.get(key) == value for key, value in query.items())
        ]

        if not records_to_delete:
            raise ValueError(f"No records found matching query: {query}")

        for record_id in records_to_delete:
            record = self.data[table][record_id]
            await self._update_index_for_record(table, record, record_id, operation='remove')
            del self.data[table][record_id]

    async def fetch_all(self):
        return self.data

