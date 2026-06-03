from homeassistant.helpers.entity import Entity
from .entity import SolMateEntity

class SolMateSensor(Entity, SolMateEntity):

    def __init__(self, coordinator, key, name):
        self.coordinator = coordinator
        self.key = key

        self._attr_name = f"SolMate {name}"
        self._attr_unique_id = f"solmate_{key}"

    @property
    def state(self):
        return self.coordinator.data.get(self.key)
