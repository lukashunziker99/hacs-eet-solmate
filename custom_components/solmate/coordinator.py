import asyncio
import json
import websockets
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from datetime import timedelta
from .write import SolMateWriter

class SolMateCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, host, port):
        super().__init__(
            hass,
            name="solmate",
            update_interval=timedelta(seconds=10),
        )

        self.host = host
        self.port = port
        self.data = {}

        self.ws_task = None
        self.running = True

        # placeholder until WS connects
        self.writer = None

    async def start(self):
        self.ws_task = self.hass.async_create_task(self._ws_loop())

    async def stop(self):
        self.running = False

    async def _ws_loop(self):
        url = f"ws://{self.host}:{self.port}"

        while self.running:
            try:
                async with websockets.connect(url) as ws:

                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)

                        self.data = {
                            "pv_power": data.get("pvPower"),
                            "battery_soc": data.get("batterySoc"),
                            "grid_power": data.get("gridPower"),
                            "consumption": data.get("consumption"),
                        }

                        # lazy init writer (once WS is alive)
                        if self.writer is None:
                            self.writer = SolMateWriter(
                                mqtt_client=None,   # optional fallback mode
                                routes=data.get("routes", {}),
                                real_names=data.get("realNames", {})
                            )

                        self.async_set_updated_data(self.data)

            except Exception:
                await asyncio.sleep(5)
