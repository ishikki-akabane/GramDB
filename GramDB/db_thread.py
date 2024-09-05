import threading
import asyncio
import time
import requests
import aiohttp
from typing import Callable, Any

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



class GramDBTaskRunner:
    def __init__(self):
        self.loop = None
        self.thread = None
        self.running = False
        self.tasks = []
        self.shutdown_event = threading.Event()
        self.loop_ready_event = threading.Event()

    def _start_loop(self):
        """Run the asyncio event loop in a separate thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.running = True
        self.loop_ready_event.set()  # Signal that the loop is ready
        self.loop.run_forever()

        # Perform final cleanup when the loop is stopped
        pending = asyncio.all_tasks(self.loop)
        if pending:
            self.loop.run_until_complete(asyncio.gather(*pending))
        self.loop.close()

    def start(self):
        """Start the thread and event loop."""
        if self.thread is None:
            self.thread = threading.Thread(target=self._start_loop, daemon=True)
            self.thread.start()

        # Wait until the event loop is ready
        self.loop_ready_event.wait()

    def create_task(self, coro):
        """Schedule an asynchronous task."""
        if not self.running:
            print("AsyncTaskRunner is not running.")
            raise RuntimeError("AsyncTaskRunner is not running.")
        print("Creating task")
        task = asyncio.run_coroutine_threadsafe(coro, self.loop)
        self.tasks.append(task)
        print("end")
        return task

    async def _shutdown(self):
        """Shut down the event loop and wait for all tasks to complete."""
        # Await each task to ensure it completes
        for task in self.tasks:
            try:
                await asyncio.wrap_future(task)
            except Exception as e:
                print(f"Task encountered an error: {e}")

        # Stop the loop
        self.loop.stop()
        
    def stop(self):
        """Stop the thread and event loop gracefully."""
        if not self.running:
            return

        self.shutdown_event.set()
        self.thread.join()
        self.running = False
        self.thread = None
        self.loop = None



class GramDBAsyncccc:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.run_loop)
        self.thread.daemon = False
        self.task_handler = TaskHandler(self.loop)

    def run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def start(self):
        self.thread.start()

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)

    def wait(self, timeout=5):
        self.stop()
        self.thread.join(timeout)
        if self.thread.is_alive():
            raise Exception("Timeout waiting for tasks to complete")

    #def __exit__(self, exc_type, exc_val, exc_tb):
    #    self.wait()

class TaskHandler:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    def create_task(self, coroutine: Callable[[], Any]):
        return self.loop.run_in_executor(None, self.loop.run_until_complete, coroutine)



class GramDBAsync:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.run_event_loop)
        self.thread.start()

    def run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def close_func(self):
        self.loop.call_soon_threadsafe(self.loop.stop)

    def close(self):
        self.close_func()
        self.thread.join()

    def run_async(self, coroutine):
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop).result()

