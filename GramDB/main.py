import requests
import aiohttp
from GramDB.method import *
from GramDB.helper import EfficientDictQuery


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
        for tablename, table in self.CACHE_TABLE.items():
            if tablename=="info_gramdb":
                pass
            self.CACHE_DATA[tablename] = {}
            result, all_rows = fetchall(self.url, self.token, table)
            for row_id, row in all_rows.items():
                self.CACHE_DATA[tablename][row_id] = row

        print(self.CACHE_DATA)
        self.db = EfficientDictQuery(self.CACHE_DATA)
        self.db.create_all_indexes()
        
        
    async def create(self, table_name: str):
        pass

    async def delete_table(self, table_name: str):
        pass

    async def insert(self, table_name: str, data):
        data = str(data)
        await insert_func(self.session, self.url, self.token, data)
        

    async def update(self, table_name: str, data_id, data):
        pass

    async def delete(self, table_name: str, data_id):
        pass

    async def fetch(self, table_name: str, data_id):
        pass

    def close(self):
        self.session.close()
  

