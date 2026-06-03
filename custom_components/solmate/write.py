import json
import logging

_LOGGER = logging.getLogger(__name__)

class SolMateWriter:

    def __init__(self, ws, mqtt_fallback=None):
        self.ws = ws
        self.mqtt = mqtt_fallback

        self.map = {
            "battery_reserve": "setBatteryReserve",
            "mode": "setMode",
            "force_charge": "setForceCharge",
        }

    async def write(self, coordinator, key, value):

        command = self.map.get(key)

        if not command:
            _LOGGER.warning("Unknown write key: %s", key)
            return

        payload = json.dumps({
            "cmd": command,
            "value": value
        })

        try:
            if self.ws:
                await self.ws.send(payload)
                return

            if self.mqtt:
                await self.mqtt.write(key, value)

        except Exception as e:
            _LOGGER.error("Write failed %s: %s", key, e)
