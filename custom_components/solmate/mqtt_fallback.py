import json
import logging

_LOGGER = logging.getLogger(__name__)

class SolMateMQTTFallback:

    def __init__(self, mqtt, base):
        self.mqtt = mqtt
        self.base = base

    async def write(self, key, value):

        try:
            topic = f"{self.base}/set/{key}"

            if self.mqtt:
                self.mqtt.publish(topic, json.dumps({"value": value}), qos=2)

        except Exception as e:
            _LOGGER.error("MQTT fallback error %s", e)
