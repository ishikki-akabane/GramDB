from collections import defaultdict

class EfficientDictQuery:
    def __init__(self, data):
        self.data = data
        self.indexes = defaultdict(dict)

    def create_index(self, field):
        index = defaultdict(list)
        for key, item in self.data.items():
            if field in item:
                index[item[field]].append(key)
        self.indexes[field] = index

    async def query(self, field, value):
        if field not in self.indexes:
            raise ValueError(f"Index for field '{field}' does not exist. Please create it first.")
        
        keys = self.indexes[field].get(value, [])
        return [{key: self.data[key]} for key in keys]

    def create_all_indexes(self):
        if not self.data:
            return

        fields = set()
        for item in self.data.values():
            fields.update(item.keys())
        
        for field in fields:
            self.create_index(field)

