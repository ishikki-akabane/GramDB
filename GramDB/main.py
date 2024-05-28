import requests


class GramDB:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.CACHE_TABLE = {}
        self.CACHE_DATA = {}
        auth = requests.get(self.db_url)

    async def create(self, table_name: str):
        pass

    async def delete(self, table_name: str):
        pass

    async def insert_data(self, table_name: str):
        pass

    async def update_data(self, table_name: str):
        pass

    async def delete_data(self, table_name: str):
        pass

    async def fetch_data(self, table_name: str):
        pass

    async def close(self):
        pass
  

