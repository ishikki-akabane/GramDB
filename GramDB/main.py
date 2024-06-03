# lmao

import requests
import aiohttp
from GramDB.method import *
from GramDB.helper import EfficientDictQuery
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
        response = requests.get(self.db_url)
        if response.status_code == 400:
            raise ValueError("Authentication failed: Invalid credentials or URL.")
        elif response.status_code != 200:
            raise ValueError(f"Authentication failed: Unexpected status code {response.status}.")
            
        # Proceed if authentication is successful
        self.auth = response.json()
        self.token = self.auth['client_id']
        self.url = self.auth['url']
        self.import_cache()

    def import_cache(self):
        result, data = extract_func(self.url, self.token)
        if result:
            self.CACHE_TABLE = data
        else:
            raise ValueError("Authentication failed: token expired or outdated!")

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
                # row = {'_m_id': '21', '_table_': 'test_table', 'id': 1234567891, 'name': "ishikki"},
                self.CACHE_DATA[row['_m_id']] = row
        else:
            raise ValueError(f"{all_rows}")        
                    
        self.db = EfficientDictQuery(self.CACHE_DATA)


    async def create(self, table_name: str, schema):
        sample_record = {field: "test" for field in schema}
        sample_record['_id'] = "sample1928"
        result, mdata = await insert_func(self.session, self.url, self.token, sample_record)
        if result:
            _m_id = mdata["data_id"]
            sample_record['_m_id'] = _m_id
            await self.db.create(table_name, schema, sample_record, _m_id)
        
    async def fetch(self, table_name: str, query: dict):
        return await self.db.fetch(table_name, query)

    async def fetch_all(self):
        return await self.db.fetch_all()

    async def insert(self, table_name: str, record: dict):
        if '_id' not in record:
            record['_id'] = await self.db._generate_random_id()

        result, mdata = await insert_func(self.session, self.url, self.token, record)
        if result:
            _m_id = mdata["data_id"]
            record['_m_id'] = _m_id
        await self.db.insert(table_name, record, _m_id=_m_id)

    async def delete(self, table_name: str, query: dict):
        _m_id = await self.db.delete(table_name, query)
        return

    async def background_update(self, table_name, update_query, _m_id):
        await asyncio.sleep(8)
        record = await self.db.fetch(table_name, update_query)
        print("test record: ", record[0])
        result, mdata = await update_func(self.session, self.url, self.token, _m_id, record[0])
        print("file inserted")
        
    async def update(self, table_name: str, query: dict, update_query: dict):
        _m_id = await self.db.update(table_name, query, update_query)
        print("added data : ", _m_id)
        await asyncio.create_task(self.background_update(table_name, update_query, _m_id))
        print("running")
        return

    async def delete_table(self, table_name: str):
        await self.db.delete_table(table_name)

    async def close_func(self):
        await self.session.close()
        
    def close(self):
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self.close_func())
        else:
            asyncio.run(self.close_func())
  

