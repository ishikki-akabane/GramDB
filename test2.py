
from datetime import datetime
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
            "batch": ("_id", "channel_id", "message_id"),
            "debug": ("chat_id", "func_name", "file_path", "error_line", "error_e")
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

    async def add_error(
        self,
        chat_id: str,
        func_name: str,
        file_path: str,
        error_line: str,
        error_e: str
    ):
        print("hola")
        current_time = datetime.now()
        str_date = current_time.strftime("%d %B, %Y %H:%M:%S")
        try:
            await self.db.insert_one(
                "debug",
                {
                    "chat_id": chat_id,
                    "func_name": func_name,
                    "file_path": file_path,
                    "error_line": error_line,
                    "error_e": error_e
                }
            )
        except Exception as e:
            LOGGER.error(f"Error adding debug info to database: {e}")
        return

    def close(self):
        self.db.close()


async def main():
    db = DATABASE("https://blue-api.vercel.app/database?client=ishikki@xyz242.gramdb")
    await db.add_error(628292929, "start_cmd", "/root/RuKa-Bot/RUKA/modules/start.py", 5, "Message.reply_text() got an unexpected keyword argument 'haha'")
    db.close()

asyncio.run(main())
