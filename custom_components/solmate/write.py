import json
import logging

_LOGGER = logging.getLogger(__name__)

class SolMateWriter:

    def __init__(self, mqtt_client, routes=None, real_names=None):
        self.mqtt = mqtt_client
        self.routes = routes or {}
        self.real_names = real_names or {}

    async def write(self, key, value):

        route = self.routes.get(key)
        real_name = self.real_names.get(key)

        if not route or not real_name:
            _LOGGER.warning("No mapping for %s", key)
            return

        payload = json.dumps({real_name: value})

        _LOGGER.debug("WRITE %s → %s", key, payload)

        if self.mqtt:
            self.mqtt.publish(route, payload, qos=2)
