import threading
import asyncio
from queue import Queue
from concurrent.futures import Future

class GramDBAsync:
    def __init__(self):
        self.background_tasks = []
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.run_event_loop, name="GramDBAsync")
        self.thread.start()
        self.running = True
        
    def run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def close_func(self):
        self.loop.call_soon_threadsafe(self.loop.stop)

    def close(self):
        """Close the event loop and stop the thread gracefully."""
        self.close_func()
        self.thread.join()

    def run_async(self, coroutine):
        """
        Schedule a coroutine to run on the GramDBAsync thread.
        """
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop).result()

    def create_task(self, coroutine):
        """
        Create a task to run the given coroutine.
        
        This method is similar to asyncio.create_task but works within the context of this class.
        
        :param coroutine: The coroutine to be executed.
        :return: The created task.
        """
        task = asyncio.run_coroutine_threadsafe(self._create_task_in_loop(coroutine), self.loop)
        return task.result()

    async def _create_task_in_loop(self, coroutine):
        """
        Create and schedule a coroutine in the running event loop.
        This helper ensures the task is created and runs inside the event loop.
        """
        task = self.loop.create_task(coroutine)
        self.background_tasks.append(task)
        return task
        
