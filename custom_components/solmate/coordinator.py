from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from datetime import timedelta
import asyncio

from .websocket import SolMateWebSocket
from .write import SolMateWriter
from .mqtt_fallback import SolMateMQTTFallback

class SolMateCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, host, port, mqtt=None):

        super().__init__(
            hass,
            name="solmate",
            update_interval=timedelta(seconds=10),
        )

        self.hass = hass
        self.host = host
        self.port = port

        self.data = {}
        self._running = True

        self.ws_client = SolMateWebSocket(host, port)

        self.writer = None
        self.mqtt_fallback = SolMateMQTTFallback(mqtt, "solmate")

    async def start(self):
        self.hass.async_create_task(self._run())

    async def stop(self):
        self._running = False

    def running(self):
        return self._running

    async def _run(self):

        async def handler(payload):

            self.data = {
                "pv_power": payload.get("pvPower"),
                "battery_soc": payload.get("batterySoc"),
                "grid_power": payload.get("gridPower"),
                "consumption": payload.get("consumption"),
                "mode": payload.get("mode"),
                "force_charge": payload.get("forceCharge"),
            }

            if self.writer is None:
                self.writer = SolMateWriter(
                    self.ws_client,
                    self.mqtt_fallback
                )

            self.async_set_updated_data(self.data)

        await self.ws_client.receive_loop(handler, self.running)
