import logging
import requests
import aiohttp
from GramDB.method import *
from GramDB.helper import EfficientDictQuery
from GramDB.exception import *
from GramDB.asyncio import *
import asyncio
import threading

logger = logging.getLogger('GramDB')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')



class GramDB:
    def __init__(self, db_url: str, async_manager):
        """
        Initialize the GramDB class with the provided database URL and async manager.
        """
        self.db_url = db_url
        self.session = None
        self.token = None
        self.url = None
        self.CACHE_TABLE = None
        self.CACHE_DATA = None
        self.db = None
        self.background_tasks = []
        self.async_manager = async_manager
        self.initialize()

    def initialize(self):
        logger.info("Authenticating GramDB credentials...")
        self.authenticate()

    def authenticate(self):
        """Authenticate with the provided database URL."""
        try:
            response = requests.get(self.db_url)
            if response.status_code == 400:
                raise ValueError("Authentication failed: Invalid credentials or URL.")
            elif response.status_code == 500:
                raise ValueError(f"Authentication failed: Server failed to respond!")
            elif response.status_code != 200:
                raise ValueError(f"Authentication failed: Unexpected status code {response.status_code}")
                                                                                  
            self.auth = response.json()
            self.token = self.auth['client_id']
            self.url = self.auth['url']
            self.import_cache()
        except Exception as e:
            raise ConnectionError(f"Network error during authentication: {e}")

    def import_cache(self):
        """Import cache data after authentication."""
        try:
            result, data = extract_func(self.url, self.token)
            if result:
                self.CACHE_TABLE = data
            else:
                raise ValidationError("Authentication failed: token expired or outdated!")
            
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
                    self.CACHE_DATA[row['_m_id']] = row
            else:
                raise GramDBError(f"Failed to fetch all data: {all_rows}")
                
            self.db = EfficientDictQuery(self.CACHE_DATA)
            logger.info(f"GramDB successfully authenticated and running...")
                
        except Exception as e:
            raise GramDBError(f"Error importing cache: {e}")

    
    async def check_table(self, table_name: str):
        """
        Check if a table exists in the database.
        :param table_name: The name of the table to check.
        :return: Boolean indicating if the table exists.
        """
        return await self.db.check_table(table_name)

    async def background_create(self, table_name, _m_id):
        try:
            result, old_data = await async_extract_func(self.url, self.token)
            old_data[table_name] = [_m_id]
            async with aiohttp.ClientSession() as newsession:
                result2, response = await git_func(newsession, self.url, self.token, old_data)
        except Exception as e:
            raise GramDBError(f"Error in background create: {e}")

    async def create(self, table_name: str, schema):
        """
        Create a new record in the specified table.
        :param table_name: The name of the table.
        :param schema: The schema for the new record.
        """
        try:
            sample_record = {field: "test" for field in schema}
            sample_record['_id'] = "sample1928"
            async with aiohttp.ClientSession() as newsession:
                result, mdata = await insert_func(newsession, self.url, self.token, sample_record, table_name)
            if result:
                _m_id = mdata["data_id"]
                sample_record['_m_id'] = _m_id
                del sample_record["_table_"]
                await self.db.create(table_name, schema, sample_record, _m_id)
                
                task = self.async_manager.create_task(self.background_create(table_name, _m_id))
                self.background_tasks.append(task)
            else:
                raise GramDBError(f"Failed to create record in table {table_name}\nError: {mdata}")
        except Exception as e:
            raise GramDBError(f"Error creating record: {e}")

    async def fetch(self, table_name: str, query: dict):
        try:
            result = await self.db.fetch(table_name, query)
            if len(result) == 0:
                return None
            elif len(result) == 1:
                return result[0]
            else:
                return result
        except Exception as e:
            raise GramDBError(f"Error fetching data: {e}")

    async def fetch_one(self, table_name: str, query: dict):
        try:
            result = await self.db.fetch(table_name, query)
            if len(result) == 0:
                return None
            else:
                return result[0]
        except Exception as e:
            raise GramDBError(f"Error fetching data: {e}")

    async def fetch_all(self):
        try:
            return await self.db.fetch_all()
        except Exception as e:
            raise GramDBError(f"Error fetching all data: {e}")

    async def background_insert(self, table_name, _m_id):
        try:
            result, old_data = await async_extract_func(self.url, self.token)
            new_data = old_data[table_name]
            new_data.append(_m_id)
            async with aiohttp.ClientSession() as newsession:
                result2, response = await git_func(newsession, self.url, self.token, old_data)
        except Exception as e:
            raise GramDBError(f"Error in background insert: {e}")

    async def insert(self, table_name: str, record: dict):
        try:
            if '_id' not in record:
                record['_id'] = await self.db._generate_random_id()

            async with aiohttp.ClientSession() as newsession:
                result, mdata = await insert_func(newsession, self.url, self.token, record, table_name)
            if result:
                _m_id = mdata["data_id"]
                record['_m_id'] = _m_id
                del record['_table_']
                await self.db.insert(table_name, record, _m_id=_m_id)
                task = self.async_manager.create_task(self.background_insert(table_name, _m_id))
                self.background_tasks.append(task)
            else:
                raise GramDBError(f"Failed to insert record in table {table_name}")
        except Exception as e:
            raise GramDBError(f"Error inserting record: {e}")

    async def background_delete(self, table_name, _m_id):
        try:
            result, old_data = await async_extract_func(self.url, self.token)
            new_data = old_data[table_name]          
            new_data.remove(int(_m_id))
            async with aiohttp.ClientSession() as newsession:
                result2, response = await git_func(newsession, self.url, self.token, old_data)
        except Exception as e:
            raise GramDBError(f"Error in background delete: {e}")

    async def delete(self, table_name: str, query: dict):
        try:
            _m_id = await self.db.delete(table_name, query)
            task = self.async_manager.create_task(self.background_delete(table_name, _m_id))
            self.background_tasks.append(task)
        except Exception as e:
            raise GramDBError(f"Error deleting record: {e}")

    async def background_update(self, table_name, query, _m_id):
        try:
            records = await self.db.fetch(table_name, query)
            async with aiohttp.ClientSession() as newsession:
                result, mdata = await update_func(newsession, self.url, self.token, _m_id, records[0], table_name)
        except Exception as e:
            raise GramDBError(f"Error in background update: {e}")

    async def update(self, table_name: str, query: dict, update_query: dict):
        try:
            _m_id = await self.db.new_update(table_name, query, update_query)
            #_m_id = await self.db.update(table_name, query, update_query)
            task = self.async_manager.create_task(self.background_update(table_name, query, _m_id))
            self.background_tasks.append(task)
        except Exception as e:
            raise GramDBError(f"Error updating record: {e}")

    async def background_delete_table(self, table_name):
        try:
            result, old_data = await async_extract_func(self.url, self.token)
            del old_data[table_name]
            async with aiohttp.ClientSession() as newsession:
                result2, response = await git_func(newsession, self.url, self.token, old_data)
        except Exception as e:
            raise GramDBError(f"Error in background delete table: {e}")
            
    async def delete_table(self, table_name: str):
        try:
            await self.db.delete_table(table_name)
            task = self.async_manager.create_task(self.background_delete_table(table_name))
            self.background_tasks.append(task)
        except Exception as e:
            raise GramDBError(f"Error deleting table {table_name}: {e}")

    
    async def wait_for_background_tasks(self):
        """Wait for all background tasks to complete."""
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks)
            print("All background tasks completed.")

    def __del__(self):
        """Ensure all background tasks are completed before exiting."""
        logger.info("Destroying asyncio tasks..")
        self.close_func()
            
    def close_func(self):
        """Close the asynchronous manager gracefully."""
        try:
            self.async_manager.close()
        except RuntimeError:
            return
        
    def close(self):
        """Run async background tasks and close the async manager."""
        self.async_manager.run_async(self.wait_for_background_tasks())
        logger.info("Closing GramDBAsync manager..")
        self.close_func()
