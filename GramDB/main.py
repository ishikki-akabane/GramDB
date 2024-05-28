import requests
import aiohttp


class GramDB:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.CACHE_TABLE = {}
        self.CACHE_DATA = {}
        self.session = aiohttp.ClientSession()
        self.authenticate()

    def authenticate(self):
        response = requests.get(self.db_url)
        if response.status == 400:
            raise ValueError("Authentication failed: Invalid credentials or URL.")
        elif response.status != 200:
            raise ValueError(f"Authentication failed: Unexpected status code {response.status}.")
            
        # Proceed if authentication is successful
        self.auth = response.json()
        self.token = response.json()['client_id']

    async def create(self, table_name: str):
        pass

    async def delete_table(self, table_name: str):
        pass

    async def insert(self, table_name: str, data):
        pass

    async def update(self, table_name: str, data_id, data):
        pass

    async def delete(self, table_name: str, data_id):
        pass

    async def fetch(self, table_name: str, data_id):
        pass

    async def close(self):
        await self.session.close()
  

