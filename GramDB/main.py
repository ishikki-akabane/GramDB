import requests
import aiohttp
from GramDB.method import *
from GramDB.helper import EfficientDictQuery
import asyncio


class GramDB:
    def __init__(self, db_url: str):
        self.db_url = db_url
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
            print(data)
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
                    
        print(self.CACHE_DATA)
        self.db = EfficientDictQuery(self.CACHE_DATA)

    
    async def fetch(self, table_name: str, query: dict):
        return await self.db.fetch(table_name, query)

    async def fetch_all(self):
        return await self.db.fetch_all()

    async def insert(self, table_name: str, record, **keargs):
        await self.db.insert(table_name, record, **keargs)
        
    async def create_table(self, table_name: str):
        pass

    async def delete_table(self, table_name: str):
        pass
        

    async def update(self, table_name: str, data_id, data):
        pass

    async def delete(self, table_name: str, data_id):
        pass


    def close(self):
        asyncio.run(self.session.close())
  

