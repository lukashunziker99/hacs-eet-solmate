import json
import logging

_LOGGER = logging.getLogger(__name__)

class SolMateMQTTFallback:

    def __init__(self, mqtt_client, base_topic):
        self.mqtt = mqtt_client
        self.base = base_topic

    async def write(self, key, value):
        try:
            topic = f"{self.base}/set/{key}"
            payload = json.dumps({"value": value})

            if self.mqtt:
                self.mqtt.publish(topic, payload, qos=2)
                _LOGGER.debug("MQTT fallback write %s", topic)

        except Exception as e:
            _LOGGER.error("MQTT fallback failed: %s", e)
