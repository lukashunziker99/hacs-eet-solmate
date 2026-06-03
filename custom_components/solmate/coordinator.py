import asyncio
import json
import websockets
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .write import SolMateWriter
from .mqtt_fallback import SolMateMQTTFallback

class SolMateCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, host, port, mqtt=None):

        super().__init__(
            hass,
            name="solmate",
            update_interval=timedelta(seconds=5),
        )

        self.host = host
        self.port = port

        self.data = {}
        self.running = True
        self.ws = None

        self.writer = None
        self.mqtt_fallback = mqtt

        self.backoff = 2

    async def start(self):
        self.hass.async_create_task(self._ws_loop())

    async def stop(self):
        self.running = False

    async def _ws_loop(self):

        url = f"ws://{self.host}:{self.port}"

        while self.running:

            try:
                async with websockets.connect(
                    url,
                    ping_interval=20,
                    ping_timeout=20
                ) as ws:

                    self.ws = ws
                    self.backoff = 2

                    # init write layer
                    self.writer = SolMateWriter(
                        ws=ws,
                        mqtt_fallback=self.mqtt_fallback
                    )

                    while self.running:

                        msg = await ws.recv()
                        payload = json.loads(msg)

                        self.data = {
                            "pv_power": payload.get("pvPower"),
                            "battery_soc": payload.get("batterySoc"),
                            "grid_power": payload.get("gridPower"),
                            "consumption": payload.get("consumption"),
                            "mode": payload.get("mode"),
                            "force_charge": payload.get("forceCharge"),
                        }

                        self.async_set_updated_data(self.data)

            except Exception:
                await asyncio.sleep(self.backoff)
                self.backoff = min(self.backoff * 2, 30)
