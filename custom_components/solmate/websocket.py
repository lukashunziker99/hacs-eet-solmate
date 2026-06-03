import asyncio
import json
import websockets
import logging

_LOGGER = logging.getLogger(__name__)

class SolMateWebSocket:

    def __init__(self, host, port):
        self.url = f"ws://{host}:{port}"
        self.ws = None

    async def connect(self):
        return await websockets.connect(self.url, ping_interval=20)

    async def receive_loop(self, callback, running_flag):

        backoff = 2

        while running_flag():

            try:
                async with await self.connect() as ws:
                    self.ws = ws
                    backoff = 2

                    while running_flag():
                        msg = await ws.recv()
                        await callback(json.loads(msg))

            except Exception as e:
                _LOGGER.warning("WS reconnect in %s sec", backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
