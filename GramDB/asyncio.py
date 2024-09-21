import threading
import asyncio
from queue import Queue
import aiohttp
from concurrent.futures import Future

class GramDBAsync:
    def __init__(self):
        self.background_tasks = set()
        self.loop = asyncio.new_event_loop()
        #self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run_async_loop, name="GramDBAsync", daemon=False)
        self.thread.start()
        self.running = True
        
        # self.task_queue = Queue()
        # self.thread = threading.Thread(target=self.run_event_loop, name="GramDBAsync")
        # self.thread.start()

    def _run_async_loop(self):
        """Run the asyncio event loop in a separate thread."""
        asyncio.set_event_loop(self.loop)
        self.running = True
        self.loop.run_forever()

    def _close_func(self):
        self.loop.call_soon_threadsafe(self.loop.stop)

    def _close(self):
        self._close_func()
        self.thread.join()

    def run_async(self, coro):
        """Schedule a coroutine to run on the GramDBAsync thread."""
        if not self.loop or not self.running:
            raise RuntimeError("GramDBAsync thread is not running.")
        task = asyncio.run_coroutine_threadsafe(coro, self.loop)
        self.background_tasks.add(task)

        # Ensure task is removed from the background tasks once done
        task.add_done_callback(self._task_done)
        return task

    def _task_done(self, task):
        """Remove completed tasks from the background task set."""
        self.background_tasks.discard(task)
        print(f"Task {task} completed.")

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
        #self.pending_tasks.append(task)
        return task
        
    async def _async_create_task(self, coroutine):
        """
        Internal helper function to create the asyncio task.
        """
        return self.loop.create_task(coroutine)

    def close(self):
        """Close the event loop and stop the thread gracefully."""
        if self.loop and self.running:
            logger.info("Waiting for all pending tasks to complete before closing.")
            # Wait for background tasks to complete before closing
            self.run_async(self.wait_for_background_tasks())
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join()
            self.running = False
            print("GramDBAsync loop stopped and thread joined.")

    async def wait_for_background_tasks(self):
        """Wait for all pending background tasks to complete."""
        pending_tasks = [t for t in self.background_tasks if not t.done()]
        
        if pending_tasks:
            print(f"Waiting for {len(pending_tasks)} pending tasks to complete.")
            await asyncio.gather(*pending_tasks)
            print("All background tasks completed.")

