from homeassistant.helpers.entity import Entity

SENSORS = {
    "pv_power": "PV Power",
    "battery_soc": "Battery SOC",
    "grid_power": "Grid Power",
    "consumption": "Consumption",
}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data["solmate"][entry.entry_id]

    async_add_entities(
        SolMateSensor(coordinator, key, name)
        for key, name in SENSORS.items()
    )

class SolMateSensor(Entity):
    def __init__(self, coordinator, key, name):
        self.coordinator = coordinator
        self.key = key
        self._attr_name = f"SolMate {name}"
        self._attr_unique_id = f"solmate_{key}"

    @property
    def state(self):
        return self.coordinator.data.get(self.key)

    @property
    def available(self):
        return self.coordinator.data is not None
