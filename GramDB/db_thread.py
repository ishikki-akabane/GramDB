import threading
import asyncio

class GramDBThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.loop = asyncio.new_event_loop()
        self.running = True

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def stop(self):
        self.running = False
        self.loop.stop()

    def submit(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop)
