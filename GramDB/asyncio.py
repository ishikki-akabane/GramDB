import threading
import asyncio
from queue import Queue
import aiohttp
from concurrent.futures import Future

class GramDBAsync:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.pending_tasks = []
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run_event_loop, name="GramDBAsync")
        self.thread.start()
        
        # self.task_queue = Queue()
        # self.thread = threading.Thread(target=self.run_event_loop, name="GramDBAsync")
        # self.thread.start()

    def run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _close_func(self):
        self.loop.call_soon_threadsafe(self.loop.stop)

    def _close(self):
        self._close_func()
        self.thread.join()

    def run_async(self, coroutine):
        """
        Run a coroutine in the event loop and return its result.
        """
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop).result()

    def _create_task(self, coroutine):
        """
        NOTICE: DEPRECATED CAUSE OF COMPATIBILITY ISSUES
        
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
        task = asyncio.run_coroutine_threadsafe(self._async_create_task(coroutine), self.loop)
        self.pending_tasks.append(task)
        return task
        
    async def _async_create_task(self, coroutine):
        """
        Internal helper function to create the asyncio task.
        """
        return self.loop.create_task(coroutine)

    def close(self):
        """
        Close the event loop and wait for all pending tasks to finish before stopping the loop.
        """
        # Ensure all tasks are finished before stopping the event loop
        self.loop.call_soon_threadsafe(self.wait_for_tasks)
        self.stop_event.wait()  # Wait for the stop signal before closing
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()

    def wait_for_tasks(self):
        """
        Wait for all tasks to complete before setting the stop event.
        """
        # Wait for all pending tasks to complete
        pending = [t for t in self.pending_tasks if not t.done()]
        if pending:
            asyncio.gather(*pending).add_done_callback(lambda _: self.stop_event.set())
        else:
            self.stop_event.set()

