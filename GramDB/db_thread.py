import threading
import asyncio
import time
import requests
import aiohttp

from GramDB.method import *
from GramDB.exception import *


class GramDBThread:
    def __init__(self, gram_db):
        self.gram_db = gram_db
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True  # Set as daemon so it stops when main thread Stop
        self._tasks = []

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()

    def _run(self):
        while not self._stop_event.is_set():
            time.sleep(1)

    async def perform_background_task(self, table_name, _m_id):
        try:
            result, old_data = await async_extract_func(self.gram_db.url, self.gram_db.token)
            old_data[table_name] = [_m_id]
            async with aiohttp.ClientSession() as newsession:
                result2, response = await git_func(newsession, self.gram_db.url, self.gram_db.token, old_data)
        except Exception as e:
            raise GramDBError(f"Error in background create: {e}")

    def start_background_task(self, table_name, _m_id):
        # Start the background task in a separate thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._tasks.append(task)
        loop.run_until_complete(self.perform_background_task(table_name, _m_id))
        loop.close()

    def start2_background_task(self, table_name, _m_id):
        loop = asyncio.new_event_loop()
        task = loop.create_task(self.perform_background_task(table_name, _m_id))
        self._tasks.append(task)
        loop.run_until_complete(task)
        loop.close()

    def wait_for_tasks(self):
        while self._tasks:
            time.sleep(0.1)
