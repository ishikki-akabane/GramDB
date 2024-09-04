
from GramDB import GramDB
import asyncio


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
        self.db = GramDB(uri)
        self.table_schemas = {
            "users": ("_id", "upload", "batch"),
            "files": ("_id", "message_id"),
            "batch": ("_id", "channel_id", "message_id")
        }
        asyncio.run(self.create_table())
        print("DATABASE Online")

    async def create_table(self):
        """
        Asynchronously creates a table if it doesn't exist.
        """
        for table_name, schema in self.table_schemas.items():
            if not await self.db.check_table(table_name):
                await self.db.create(table_name, schema)


db = DATABASE("https://blue-api.vercel.app/database?client=ishikki@xyz242.gramdb")
