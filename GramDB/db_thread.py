import threading
import asyncio
import time


class GramDBThread:
    def __init__(self, gram_db):
        self.gram_db = gram_db
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True  # Set as daemon so it stops when main thread stops

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
            result, old_data = async_extract_func(self.gram_db.url, self.gram_db.token)
            old_data[table_name] = [_m_id]
            async with aiohttp.ClientSession() as newsession:
                result2, response = await git_func(newsession, self.gram_db.url, self.gram_db.token, old_data)
        except Exception as e:
            raise GramDBError(f"Error in background create: {e}")

    def start_background_task(self, table_name, _m_id):
        # Start the background task in a separate thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.perform_background_task(table_name, _m_id))
        loop.close()
