import threading
import asyncio
from queue import Queue

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
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop).result()

    def create_task(self, coroutine):
        """
        Create a task to run the given coroutine.
        
        This method is similar to asyncio.create_task but works within the context of this class.
        
        :param coroutine: The coroutine to be executed.
        :return: The created task.
        """
        task_future = asyncio.Future()
        self.loop.call_soon_threadsafe(self._create_task, coroutine, task_future)
        return task_future.result()

    def _create_task(self, coroutine, task_future):
        task = self.loop.create_task(coroutine)
        task_future.set_result(task)
        # Ensure the task is added to the queue if needed
        self.task_queue.put(task)

