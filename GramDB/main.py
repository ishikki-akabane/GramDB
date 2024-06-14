import requests
import aiohttp
from GramDB.method import *
from GramDB.helper import EfficientDictQuery
from GramDB.exception import *
import asyncio

class GramDB:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.session = None
        self.token = None
        self.url = None
        self.CACHE_TABLE = None
        self.CACHE_DATA = None
        self.db = None
        self.initialize()

    def initialize(self):
        self.session = aiohttp.ClientSession()
        self.authenticate()

    def authenticate(self):
        try:
            response = requests.get(self.db_url)
            if response.status_code == 400:
                raise ValueError("Authentication failed: Invalid credentials or URL.")
            elif response.status_code != 200:
                raise ValueError(f"Authentication failed: Unexpected status code {response.status_code}")
                                                                                  
            self.auth = response.json()
            self.token = self.auth['client_id']
            self.url = self.auth['url']
            self.import_cache()
        
        except Exception as e:
            raise ConnectionError(f"Network error during authentication: {e}")

    def import_cache(self):
        try:
            result, data = extract_func(self.url, self.token)
            if result:
                self.CACHE_TABLE = data
            else:
                raise ValidationError("Authentication failed: token expired or outdated!")
            
            self.CACHE_DATA = {}
            all_ids = []
            for tablename, table in self.CACHE_TABLE.items():
                if tablename=="info_gramdb":
                    pass
                else:
                    all_ids = all_ids + table
                
            result, all_rows = fetchall_func(self.url, self.token, all_ids)
            if result:
                for row in all_rows["data"]:
                    self.CACHE_DATA[row['_m_id']] = row
            else:
                raise GramDBError(f"Failed to fetch all data: {all_rows}")
                
            self.db = EfficientDictQuery(self.CACHE_DATA)
        except Exception as e:
            raise GramDBError(f"Error importing cache: {e}")

    async def background_create(self, table_name, _m_id):
        try:
            result, old_data = extract_func(self.url, self.token)
            old_data[table_name] = [_m_id]
            result2, response = await git_func(self.session, self.url, self.token, old_data)
        except Exception as e:
            raise GramDBError(f"Error in background create: {e}")

    async def create(self, table_name: str, schema):
        try:
            sample_record = {field: "test" for field in schema}
            sample_record['_id'] = "sample1928"
            result, mdata = await insert_func(self.session, self.url, self.token, sample_record, table_name)
            if result:
                _m_id = mdata["data_id"]
                sample_record['_m_id'] = _m_id
                del sample_record["_table_"]
                await self.db.create(table_name, schema, sample_record, _m_id)
                asyncio.create_task(self.background_create(table_name, _m_id))
            else:
                raise GramDBError(f"Failed to create record in table {table_name}")
        except Exception as e:
            raise GramDBError(f"Error creating record: {e}")

    async def fetch(self, table_name: str, query: dict):
        try:
            result = await self.db.fetch(table_name, query)
            print(result)
            #if not result:
            #    raise NotFoundError(f"Record not found in table {table_name} for query {query}")
            if len(result) == 0:
                return None
            elif len(result) == 1:
                return result[0]
            else:
                return result
        except Exception as e:
            raise GramDBError(f"Error fetching data: {e}")

    async def fetch_all(self):
        try:
            return await self.db.fetch_all()
        except Exception as e:
            raise GramDBError(f"Error fetching all data: {e}")

    async def background_insert(self, table_name, _m_id):
        try:
            result, old_data = extract_func(self.url, self.token)
            new_data = old_data[table_name]
            new_data.append(_m_id)
            result2, response = await git_func(self.session, self.url, self.token, old_data)
        except Exception as e:
            raise GramDBError(f"Error in background insert: {e}")

    async def insert(self, table_name: str, record: dict):
        try:
            if '_id' not in record:
                record['_id'] = await self.db._generate_random_id()

            result, mdata = await insert_func(self.session, self.url, self.token, record, table_name)
            if result:
                _m_id = mdata["data_id"]
                record['_m_id'] = _m_id
                del record['_table_']
                await self.db.insert(table_name, record, _m_id=_m_id)
                asyncio.create_task(self.background_insert(table_name, _m_id))
            else:
                raise GramDBError(f"Failed to insert record in table {table_name}")
        except Exception as e:
            raise GramDBError(f"Error inserting record: {e}")

    async def background_delete(self, table_name, _m_id):
        try:
            result, old_data = extract_func(self.url, self.token)
            new_data = old_data[table_name]          
            new_data.remove(int(_m_id))
            result2, response = await git_func(self.session, self.url, self.token, old_data)
        except Exception as e:
            raise GramDBError(f"Error in background delete: {e}")

    async def delete(self, table_name: str, query: dict):
        try:
            _m_id = await self.db.delete(table_name, query)
            asyncio.create_task(self.background_delete(table_name, _m_id))
        except Exception as e:
            raise GramDBError(f"Error deleting record: {e}")

    async def background_update(self, table_name, update_query, _m_id):
        try:
            await asyncio.sleep(8)
            records = await self.db.fetch(table_name, update_query)       
            result, mdata = await update_func(self.session, self.url, self.token, _m_id, records[0], table_name)
        except Exception as e:
            raise GramDBError(f"Error in background update: {e}")

    async def update(self, table_name: str, query: dict, update_query: dict):
        try:
            _m_id = await self.db.update(table_name, query, update_query)
            asyncio.create_task(self.background_update(table_name, update_query, _m_id))
        except Exception as e:
            raise GramDBError(f"Error updating record: {e}")

    async def background_delete_table(self, table_name):
        try:
            result, old_data = extract_func(self.url, self.token)
            del old_data[table_name]          
            result2, response = await git_func(self.session, self.url, self.token, old_data)
        except Exception as e:
            raise GramDBError(f"Error in background delete table: {e}")
            
    async def delete_table(self, table_name: str):
        try:
            await self.db.delete_table(table_name)
            asyncio.create_task(self.background_delete_table(table_name))
        except Exception as e:
            raise GramDBError(f"Error deleting table {table_name}: {e}")

    async def close_func(self):
        await self.session.close()
        
    def close(self):
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self.close_func())
        else:
            asyncio.run(self.close_func())
