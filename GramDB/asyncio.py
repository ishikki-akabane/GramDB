import threading
import asyncio
from queue import Queue
import aiohttp
from concurrent.futures import Future

class GramDBAsync:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.task_queue = Queue()
        self.thread = threading.Thread(target=self.run_event_loop, name="GramDBAsync")
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
        """
        Run a coroutine in the event loop and return its result.
        """
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop).result()

    def _create_task(self, coroutine):
        """
        Create a task to run the given coroutine.
        
        This method is similar to asyncio.create_task but works within the context of this class.
        
        :param coroutine: The coroutine to be executed.
        :return: The created task.
        """
        task = self.loop.create_task(coroutine)
        return task



            
    def create_task(self, coroutine):
        """
        Schedule a coroutine to run in the background without blocking.
        """
        return asyncio.run_coroutine_threadsafe(self._async_create_task(coroutine), self.loop)
        
    async def _async_create_task(self, coroutine):
        """
        Internal helper function to create the asyncio task.
        """
        return self.loop.create_task(coroutine)

