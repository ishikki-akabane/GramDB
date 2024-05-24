import aiohttp,requests


class GramDB:
    db_url = None
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = aiohttp.ClientSession()
        self.CACHE_TABLE = {}
        self.CACHE_DATA = {}
        auth = requests.get(db_url,headers={'api-key':self.api_key})
        if not auth:
            raise GramDBError("Text")

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

    async def get_data(self, table_name: str):
        pass

    async def close(self):
        await self.session.close()
  

