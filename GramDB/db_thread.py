import threading
import asyncio

class GramDBAsync:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
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

