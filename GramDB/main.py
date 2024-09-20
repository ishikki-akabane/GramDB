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
    """
    The main class for interacting with GramDB, providing methods for authentication, data manipulation, and background tasks.
    """
    def __init__(self, db_url: str, async_manager):
        """
        Initialize the GramDB class with the provided database URL and async manager.

        :param db_url: The URL of the database.
        :param async_manager: The asynchronous manager instance.
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
        """
        Initialize the GramDB instance by authenticating with the provided URL.
        """
        logger.info("Authenticating GramDB credentials...")
        self.authenticate()

    def authenticate(self):
        """
        Authenticate with the provided database URL.

        :raises ValueError: If authentication fails due to invalid credentials or URL.
        :raises ConnectionError: If there is a network error during authentication.
        """
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
        """
        Import cache data after successful authentication.

        :raises GramDBError: If there is an error importing the cache.
        """
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
        """
        Create a new table in the background.

        :param table_name: The name of the table to create.
        :param _m_id: The metadata ID for the new table.
        :raises GramDBError: If there is an error in the background create operation.
        """
        try:
            async with aiohttp.ClientSession() as newsession:
                result2, response = await bg_create_func(newsession, self.url, self.token, table_name, _m_id)
        except Exception as e:
            raise GramDBError(f"Error in background create: {e}")

    async def create_one(self, table_name: str, schema):
        """
        Create a new table with the given schema.

        :param table_name: The name of the table to create.
        :param schema: The schema for the new table.
        :raises GramDBError: If there is an error creating the table.
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

    async def find(self, table_name: str, query: dict):
        """
        Fetch records from the specified table based on the given query.

        :param table_name: The name of the table to query.
        :param query: A dictionary containing the query criteria.
        :return: The fetched records List
        :raises GramDBError: If there is an error fetching data.
        """
        try:
            result = await self.db.fetch(table_name, query)
            if len(result) == 0:
                return []
            else:
                return result
        except Exception as e:
            raise GramDBError(f"Error fetching data: {e}")

    async def find_one(self, table_name: str, query: dict):
        """
        Fetch one record from the specified table based on the given query.

        :param table_name: The name of the table to query.
        :param query: A dictionary containing the query criteria.
        :return: The first matching record or None if no records match.
        :raises GramDBError: If there is an error fetching data.
        """
        try:
            result = await self.db.fetch(table_name, query)
            if len(result) == 0:
                return None
            else:
                return result[0]
        except Exception as e:
            raise GramDBError(f"Error fetching data: {e}")

    async def find_all(self):
        """
        Fetch all records from all tables.

        :return: A dictionary containing all records.
        :raises GramDBError: If there is an error fetching data.
        """
        try:
            return await self.db.fetch_all()
        except Exception as e:
            raise GramDBError(f"Error fetching all data: {e}")

    async def background_insert(self, table_name, _m_id):
        """
        Insert a new record in the background.

        :param table_name: The name of the table to insert into.
        :param _m_id: The metadata ID for the new record.
        :raises GramDBError: If there is an error in the background insert operation.
        """
        try:
            async with aiohttp.ClientSession() as newsession:
                result2, response = await bg_insert_func(newsession, self.url, self.token, table_name, _m_id)
        except Exception as e:
            raise GramDBError(f"Error in background insert: {e}")

    async def insert_one(self, table_name: str, record: dict):
        """
        Insert a new record into the specified table.

        :param table_name: The name of the table to insert into.
        :param record: The record to insert.
        :raises GramDBError: If there is an error inserting the record.
        """
        try:
            if '_id' not in record:
                record['_id'] = await self.db._generate_random_id()
                
            async with aiohttp.ClientSession() as newsession:
                result, mdata = await insert_func(newsession, self.url, self.token, record, table_name)
            if result:
                _m_id = mdata["data_id"]
                record['_m_id'] = _m_id
                del record['_table_']
                await self.db.insert_one(table_name, record, _m_id=_m_id)
                task = self.async_manager.create_task(self.background_insert(table_name, _m_id))
                self.background_tasks.append(task)
            else:
                raise GramDBError(f"Failed to insert record in table {table_name}\n{mdata}")
        except Exception as e:
            raise GramDBError(f"Error inserting record: {e}")

    async def background_delete(self, table_name, _m_id):
        """
        Delete a record in the background.

        :param table_name: The name of the table to delete from.
        :param _m_id: The metadata ID of the record to delete.
        :raises GramDBError: If there is an error in the background delete operation.
        """
        try:
            async with aiohttp.ClientSession() as newsession:
                result2, response = await bg_delete_func(newsession, self.url, self.token, table_name, _m_id)
        except Exception as e:
            raise GramDBError(f"Error in background delete: {e}")

    async def delete_one(self, table_name: str, query: dict):
        """
        Delete records from the specified table based on the given query.

        :param table_name: The name of the table to delete from.
        :param query: A dictionary containing the query criteria.
        :raises GramDBError: If there is an error deleting the record.
        """
        try:
            _m_id = await self.db.delete_one(table_name, query)
            task = self.async_manager.create_task(self.background_delete(table_name, _m_id))
            self.background_tasks.append(task)
        except Exception as e:
            raise GramDBError(f"Error deleting record: {e}")

    async def background_update(self, table_name, query, _m_id):
        """
        Update records in the background.

        :param table_name: The name of the table to update.
        :param query: A dictionary containing the query criteria.
        :param _m_id: The metadata ID of the record to update.
        :raises GramDBError: If there is an error in the background update operation.
        """
        try:
            records = await self.db.fetch(table_name, query)
            async with aiohttp.ClientSession() as newsession:
                result, mdata = await update_func(newsession, self.url, self.token, _m_id, records[0], table_name)
        except Exception as e:
            raise GramDBError(f"Error in background update: {e}")

    async def update_one(self, table_name: str, query: dict, update_query: dict):
        """
        Update records in the specified table based on the given query and update criteria.

        :param table_name: The name of the table to update.
        :param query: A dictionary containing the query criteria.
        :param update_query: A dictionary containing the update operations.
        :raises GramDBError: If there is an error updating the record.
        """
        try:
            _m_id, _id = await self.db.update_one(table_name, query, update_query)
            new_query = {"_id": _id}
            task = self.async_manager.create_task(self.background_update(table_name, new_query, _m_id))
            self.background_tasks.append(task)
        except Exception as e:
            raise GramDBError(f"Error updating record: {e}")

    async def background_delete_table(self, table_name):
        """
        Delete a table in the background.

        :param table_name: The name of the table to delete.
        :raises GramDBError: If there is an error in the background delete table operation.
        """
        try:
            async with aiohttp.ClientSession() as newsession:
                result2, response = await bg_delete_table_func(newsession, self.url, self.token, table_name)
        except Exception as e:
            raise GramDBError(f"Error in background delete table: {e}")
            
    async def delete_table(self, table_name: str):
        """
        Delete the specified table.

        :param table_name: The name of the table to delete.
        :raises GramDBError: If there is an error deleting the table.
        """
        try:
            await self.db.delete_table(table_name)
            task = self.async_manager.create_task(self.background_delete_table(table_name))
            self.background_tasks.append(task)
        except Exception as e:
            raise GramDBError(f"Error deleting table {table_name}: {e}")

    
    async def wait_for_background_tasks(self):
        """
        Wait for all background tasks to complete.

        This method ensures that all asynchronous tasks are finished before proceeding.
        """
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks)
            print("All background tasks completed.")

    def __del__(self):
        """
        Ensure all background tasks are completed before exiting.

        This destructor method ensures that all asynchronous tasks are finished when the instance is destroyed.
        """
        logger.info("Destroying asyncio tasks..")
        self.close_func()
            
    def close_func(self):
        """
        Close the asynchronous manager gracefully.

        This method closes the asynchronous manager, ensuring that all tasks are properly cleaned up.
        """
        try:
            self.async_manager.close()
        except RuntimeError:
            return
        
    def close(self):
        """
        Run async background tasks and close the async manager.

        This method runs the `wait_for_background_tasks` method and then closes the asynchronous manager.
        """
        self.async_manager.run_async(self.wait_for_background_tasks())
        logger.info("Closing GramDBAsync manager..")
        self.close_func()

