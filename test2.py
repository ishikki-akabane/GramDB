
from GramDB import GramDB, GramDBAsync
import asyncio
import threading
import logging


FORMAT = "[TEST] %(message)s"
logging.basicConfig(
    handlers=[logging.FileHandler("logs.txt"), logging.StreamHandler()],
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
)

LOGGER = logging.getLogger('[TEST]')

class DATABASE:
    """
    A class to manage the database operations using GramDB.

    Attributes:
        db (GramDB): An instance of the GramDB class initialized with the provided URI.
        table_schemas (dict): A dictionary defining table names and their corresponding schema.
    """
    
    def __init__(self, uri):
        """
        Initializes the Database instance and creates tables if they don't exist.

        Args:
            uri (str): The URI string to connect to the GramDB database.
        """
        self.async_manager = GramDBAsync()
        self.db = GramDB(uri, self.async_manager)
        self.table_schemas = {
            "users": ("_id", "uploads", "batch"),
            "files": ("_id", "message_id"),
            "batch": ("_id", "channel_id", "message_id")
        }
        self.async_manager.run_async(self.create_table())

    async def create_table(self):
        """
        Asynchronously creates a table if it doesn't exist.
        """
        for table_name, schema in self.table_schemas.items():
            if not await self.db.check_table(table_name):
                await self.db.create(table_name, schema)

    async def check_user(self, user_id: int):
        data = await self.db.fetch_one(
            "users",
            {
                "_id": user_id
            }
        )
        if data:
            return data
        else:
            return None
                
    async def add_user(self, user_id: int):
        data = await self.check_user(user_id)
        if data:
            return
        else:
            try:
                await self.db.insert(
                    "users",
                    {
                        "_id": user_id,
                        "uploads": [],
                        "batch": []
                    }
                )
            except Exception as e:
                LOGGER.error(f"Error adding user to database: {e}")
            return

    async def update(self, table_name, query, update_query):
        await self.db.update(table_name, query, update_query)

    def close(self):
        self.db.close()


async def main():
    db = DATABASE("https://blue-api.vercel.app/database?client=ishikki@xyz242.gramdb")
    await db.add_user(2233445511)
    await db.update("users", {"_id": 2233445511}, {"$pull": {"uploads": "first_element"}})
    db.close()

asyncio.run(main())
