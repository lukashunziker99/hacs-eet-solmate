import json
import logging

_LOGGER = logging.getLogger(__name__)

class SolMateWriter:

    def __init__(self, ws_client, mqtt_fallback=None):
        self.ws = ws_client
        self.mqtt = mqtt_fallback

        self.map = {
            "battery_reserve": "setBatteryReserve",
            "mode": "setMode",
            "force_charge": "setForceCharge",
        }

    async def write(self, coordinator, key, value):

        cmd = self.map.get(key)

        if not cmd:
            _LOGGER.warning("Unknown key %s", key)
            return

        payload = json.dumps({
            "cmd": cmd,
            "value": value
        })

        try:
            if self.ws and self.ws.ws:
                await self.ws.ws.send(payload)
                return

            if self.mqtt:
                await self.mqtt.write(key, value)

        except Exception as e:
            _LOGGER.error("Write failed %s", e)
