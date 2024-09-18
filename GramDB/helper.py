from collections import defaultdict
import random
import string


class EfficientDictQuery:
    """
    A class designed to efficiently manage and query data stored in a dictionary-based structure.
    
    It supports creating tables, inserting, updating, and deleting records, as well as fetching data based on queries.
    """

    def __init__(self, data):
        """
        Initializes the EfficientDictQuery instance with the given data.

        :param data: A dictionary containing the initial data to be structured.
        """
        self.data = self._structure_data(data)
        self.indexes = defaultdict(lambda: defaultdict(list))
        self.schemas = {}
        self.create_all_indexes()
        self.create_all_schemas()

    def _structure_data(self, data):
        """
        Structures the input data into a nested dictionary format suitable for the class.

        :param data: A dictionary containing records with '_table_' and '_id' keys.
        :return: A nested dictionary where each table is a key and its value is another dictionary of records.
        """
        structured_data = defaultdict(dict)
        for record in data.values():
            table = record['_table_']
            primary_key = record['_id']
            structured_record = {k: v for k, v in record.items() if k not in ['_table_']}
            structured_data[table][str(primary_key)] = structured_record
        return structured_data

    def create_all_indexes(self):
        """
        Creates indexes for all fields across all tables in the data.

        This method is called during initialization to ensure all fields are indexed.
        """
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
        """
        Creates an index for a specific field across all tables.

        :param field: The field for which the index is to be created.
        """
        index = defaultdict(list)
        for table_name, table in self.data.items():
            for key, item in table.items():
                flattened_item = self._flatten_dict(item)
                if field in flattened_item:
                    index[flattened_item[field]].append((table_name, key))
        self.indexes[field] = index

    def _flatten_dict(self, d, parent_key='', sep='.'):
        """
        Flattens a nested dictionary into a single-level dictionary.

        :param d: The dictionary to be flattened.
        :param parent_key: The parent key for nested fields.
        :param sep: The separator used to join nested keys.
        :return: A flattened dictionary.
        """
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

    def create_all_schemas(self):
        """
        Creates schemas for all tables in the data.

        This method is called during initialization to ensure all tables have defined schemas.
        """
        for table_name, records in self.data.items():
            if table_name not in self.schemas:
                schema = set()
                for record in records.values():
                    schema.update(record.keys())
                self.schemas[table_name] = tuple(schema)
    
    async def fetch(self, table, query):
        """
        Fetches records from a table based on the given query.

        :param table: The name of the table to query.
        :param query: A dictionary containing the query criteria.
        :return: A list of records that match the query.
        """
        results = []

        for record_id, record in self.data.get(table, {}).items():
            if all(record.get(key) == value for key, value in query.items()):
                results.append(record)

        return results

    async def _update_index_for_record(self, table, record, record_id, operation='add'):
        """
        Updates the index for a record in the given table.

        :param table: The name of the table.
        :param record: The record to update the index for.
        :param record_id: The ID of the record.
        :param operation: The operation to perform ('add' or 'remove').
        """
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
        """
        Validates a record against the schema of the given table.

        :param table: The name of the table.
        :param record: The record to validate.
        :raises ValueError: If the record does not match the schema.
        """
        if table not in self.schemas:
            raise ValueError(f"Table '{table}' does not exist.")

        schema = self.schemas[table]
        for field in schema:
            if field not in record:
                raise ValueError(f"Missing required field '{field}' in record for table '{table}'.")

        for field in record:
            if field not in schema:
                raise ValueError(f"Field '{field}' is not allowed in schema for table '{table}'.")

    async def check_table(self, table):
        """
        Checks if a table exists in the data.

        :param table: The name of the table to check.
        :return: True if the table exists, False otherwise.
        """
        if table not in self.schemas:
            return False
        else:
            return True
    
    async def create(self, table, schema, sample_record, _m_id):
        """
        Creates a new table with the given schema and sample record.

        :param table: The name of the table to create.
        :param schema: A list of fields in the schema.
        :param sample_record: A sample record for the table.
        :param _m_id: The metadata ID for the table.
        :raises ValueError: If the table already exists.
        """
        if table in self.data:
            raise ValueError(f"Table '{table}' already exists.")

        schema = set(schema)
        schema.update(["_id", "_m_id"])
        self.schemas[table] = tuple(schema)

        self.data[table] = {"sample1928": sample_record}
        await self._update_index_for_record(table, sample_record, "sample1928", operation='add')

    async def _generate_random_id(self):
        """
        Generates a random ID.

        :return: A random 10-character ID.
        """
        return ''.join(random.choices(string.ascii_letters + string.digits, k=20))
                               
    async def insert_one(self, table, record, **kwargs):
        """
        Inserts a new record into the given table.

        :param table: The name of the table to insert into.
        :param record: The record to insert.
        :param kwargs: Additional keyword arguments, including '_m_id'.
        :raises ValueError: If the table does not exist or if '_m_id' is missing.
        """
        _m_id = kwargs.get('_m_id')
        if not _m_id:
            raise ValueError("Record must contain '_m_id' as a keyword argument.")

        if table not in self.data:
            raise ValueError(f"Invalid table name '{table}'. Table does not exist.")
            
        _id = str(record['_id'])
        record['_m_id'] = _m_id

        await self._validate_record(table, record)

        if _id in self.data[table]:
            raise ValueError(f"Record with _id '{_id}' already exists in table '{table}'.")

        self.data[table][_id] = record
        await self._update_index_for_record(table, record, _id, operation='add')

    # deprecated - supports only set
    async def old_update(self, table, query, update_fields):
        """
        **Deprecated**: Updates a record in the given table based on the query.

        **Note**: This method only supports updating a single record and is deprecated in favor of the `update` method.

        :param table: The name of the table to update.
        :param query: A dictionary containing the query criteria.
        :param update_fields: A dictionary containing the fields to update.
        :raises ValueError: If the table does not exist or if no records match the query.
        """
        if table not in self.data:
            raise ValueError(f"Table '{table}' does not exist.")

        records_to_update = [
            (record_id, record) for record_id, record in self.data[table].items()
            if all(record.get(key) == value for key, value in query.items())
        ]

        if not records_to_update:
            raise ValueError(f"No records found matching query: {query}")

        record_id, old_record = records_to_update[0]
        _m_id = old_record["_m_id"]
        combined_record = {**old_record, **update_fields}
        await self._validate_record(table, combined_record)
        await self._update_index_for_record(table, old_record, record_id, operation='remove')

        self.data[table][record_id].update(update_fields)
        await self._update_index_for_record(table, self.data[table][record_id], record_id, operation='add')
        return _m_id

    async def update_one(self, table, query, update_fields):
        """
        Updates records in the given table based on the query.

        :param table: The name of the table to update.
        :param query: A dictionary containing the query criteria.
        :param update_fields: A dictionary containing update operations.
            Supported operations are:
                - `$set`: Set values directly.
                - `$push`: Append to a list field.
                - `$pull`: Remove from a list field.
                - `$inc`: Increment a numeric field.
        :raises ValueError: If the table does not exist or if no records match the query.
        """
        if table not in self.data:
            raise ValueError(f"Table '{table}' does not exist.")

        records_to_update = [
            (record_id, record) for record_id, record in self.data[table].items()
            if all(record.get(key) == value for key, value in query.items())
        ]

        if not records_to_update:
            raise ValueError(f"No records found matching query: {query}")

        record_id, old_record = records_to_update[0]
        _m_id = old_record["_m_id"]
        _id = old_record["_id"]

        new_record = old_record.copy()

        for operator, updates in update_fields.items():
            if operator == "$set":
                # Set values directly
                new_record.update(updates)

            elif operator == "$push":
                for key, value in updates.items():
                    if key in new_record and isinstance(new_record[key], list):
                        new_record[key].append(value)  # Append to the list
                    else:
                        raise ValueError(f"Cannot push to non-list field '{key}'")

            elif operator == "$pull":
                for key, value in updates.items():
                    if key in new_record and isinstance(new_record[key], list):
                        new_record[key] = [item for item in new_record[key] if item != value]  # Remove matching value
                    else:
                        raise ValueError(f"Cannot pull from non-list field '{key}'")

            elif operator == "$inc":
                for key, value in updates.items():
                    if key in new_record and isinstance(new_record[key], (int, float)):
                        new_record[key] += value  # Increment the value
                    else:
                        raise ValueError(f"Cannot increment non-numeric field '{key}'")

        await self._validate_record(table, new_record)

        await self._update_index_for_record(table, old_record, record_id, operation='remove')
        self.data[table][record_id] = new_record
        await self._update_index_for_record(table, self.data[table][record_id], record_id, operation='add')

        return _m_id, _id
    
    async def delete_one(self, table, query):
        """
        Deletes records from the given table based on the query.

        :param table: The name of the table to delete from.
        :param query: A dictionary containing the query criteria.
        :raises ValueError: If the table does not exist or if no records match the query.
        """
        if table not in self.data:
            raise ValueError(f"Table '{table}' does not exist.")

        records_to_delete = [
            record_id for record_id, record in self.data[table].items()
            if all(record.get(key) == value for key, value in query.items())
        ]

        if not records_to_delete:
            raise ValueError(f"No records found matching query: {query}")

        record_id = records_to_delete[0]
        record = self.data[table][record_id]
        _m_id = record["_m_id"]
        await self._update_index_for_record(table, record, record_id, operation='remove')
        del self.data[table][record_id]
        return _m_id

    async def delete_table(self, table):
        """
        Deletes the entire table and its associated schema.

        :param table: The name of the table to delete.
        :raises ValueError: If the table does not exist.
        """
        if table not in self.data:
            raise ValueError(f"Table '{table}' does not exist.")

        for record_id, record in self.data[table].items():
            await self._update_index_for_record(table, record, record_id, operation='remove')

        del self.data[table]
        del self.schemas[table]

    async def fetch_all(self, table=None):
        """
        Fetches all records from the given table or all tables if no table is specified.

        :param table: The name of the table to fetch records from. If None, fetches records from all tables.
        :return: A dictionary containing the records.
        """
        if table:
            return self.data[table]
        return self.data

