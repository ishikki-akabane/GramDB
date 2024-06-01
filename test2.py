import aiohttp
import asyncio
import json

async def insert_func(session, base_url, token, data):
    url = base_url + "/insert"
    headers = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    data = json.dumps(data)
    payload = {
        "data": str(data)
    }
    async with session.post(url, headers=headers, json=payload) as response:
        if response.status == 200:
            result = await response.json()
            return True, result
        else:
            return False, response.status

class SimpleDBClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self.session = aiohttp.ClientSession()

    async def insert(self, data):
        result, response = await insert_func(self.session, self.base_url, self.token, data)
        return result, response

    async def close(self):
        await self.session.close()

# Example usage
async def main():
    base_url = "https://gramdb-api.onrender.com"
    token = "6969696969_hehe"
    data = {"key": "value"}

    client = SimpleDBClient(base_url, token)
    
    success, response = await client.insert(data)
    if success:
        print("Insert successful:", response)
    else:
        print("Insert failed with status:", response)
    
    await client.close()

# Running the example
asyncio.run(main())
