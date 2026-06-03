import json
import logging

_LOGGER = logging.getLogger(__name__)

class SolMateWriter:

    def __init__(self, ws, mqtt_fallback=None):
        self.ws = ws
        self.mqtt = mqtt_fallback

        # static mapping (can later move to const.py)
        self.map = {
            "battery_reserve": "setBatteryReserve",
            "mode": "setMode",
            "force_charge": "setForceCharge",
        }

    async def write(self, coordinator, key, value):

        try:
            command = self.map.get(key)

            if not command:
                _LOGGER.warning("No command mapping for %s", key)
                return

            payload = json.dumps({
                "cmd": command,
                "value": value
            })

            # PRIMARY: WebSocket
            if self.ws:
                await self.ws.send(payload)
                _LOGGER.debug("WS write %s", payload)
                return

            # FALLBACK: MQTT
            if self.mqtt:
                await self.mqtt.write(key, value)
                return

        except Exception as e:
            _LOGGER.error("Write failed %s: %s", key, e)
