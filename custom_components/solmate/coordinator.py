from datetime import timedelta
import asyncio
import json
import websockets
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

class SolMateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, host, port):
        super().__init__(
            hass,
            logger=None,
            name="solmate",
            update_interval=timedelta(seconds=10),
        )

        self.host = host
        self.port = port
        self.data = {}
        self._ws_task = None
        self._running = True

    async def start(self):
        self._ws_task = self.hass.async_create_task(self._ws_loop())

    async def _ws_loop(self):
        url = f"ws://{self.host}:{self.port}"

        while self._running:
            try:
                async with websockets.connect(url) as ws:
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)

                        # 🔥 MAPPING (anpassbar!)
                        self.data = {
                            "pv_power": data.get("pvPower"),
                            "battery_soc": data.get("batterySoc"),
                            "grid_power": data.get("gridPower"),
                            "consumption": data.get("consumption"),
                            "battery_power": data.get("batteryPower"),
                        }

                        self.async_set_updated_data(self.data)

            except Exception:
                await asyncio.sleep(5)

    async def stop(self):
        self._running = False
