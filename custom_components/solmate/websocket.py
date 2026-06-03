import asyncio
import json
import websockets
import logging

_LOGGER = logging.getLogger(__name__)

class SolMateWebSocket:

    def __init__(self, host, port):
        self.url = f"ws://{host}:{port}"
        self.ws = None

    async def run(self, handler, running):

        backoff = 2

        while running():

            try:
                async with websockets.connect(
                    self.url,
                    ping_interval=20,
                    ping_timeout=20
                ) as ws:

                    self.ws = ws
                    backoff = 2

                    while running():
                        msg = await ws.recv()
                        await handler(json.loads(msg))

            except Exception as e:
                _LOGGER.warning("WS reconnect in %s sec (%s)", backoff, e)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
