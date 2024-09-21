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
        Run a coroutine in the GramDBAsync thread and block until it completes.
        
        This method behaves like asyncio.run().
        
        :param coroutine: The coroutine to run.
        :return: The result of the coroutine.
        """
        if not asyncio.iscoroutine(coroutine):
            raise ValueError("The provided argument must be a coroutine.")

        # Schedule the coroutine and block until it's done
        future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        
        # Wait for the result
        return future.result()

    def create_task(self, coroutine):
        """
        Create a task to run the given coroutine.
        
        This method is similar to asyncio.create_task but works within the context of this class.
        
        :param coroutine: The coroutine to be executed.
        :return: The created task.
        """
        self.loop.call_soon_threadsafe(self._create_task_in_loop, coroutine)
        # task = asyncio.create_task(coroutine)
        # self.background_tasks.append(task)

    def _create_task_in_loop(self, coroutine):
        """
        Create and schedule a coroutine in the running event loop.
        This helper ensures the task is created and runs inside the event loop.
        """
        task = self.loop.create_task(coroutine)
        self.background_tasks.append(task)

    async def wait_for_background_tasks(self):
        """Wait for all background tasks to complete."""
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks)
        
