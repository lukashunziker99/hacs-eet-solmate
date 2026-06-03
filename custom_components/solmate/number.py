from homeassistant.components.number import NumberEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data

    async_add_entities([
        SolMateNumber(coordinator, "battery_reserve", 0, 100)
    ])

class SolMateNumber(NumberEntity):
    def __init__(self, coordinator, key, min_v, max_v):
        self.coordinator = coordinator
        self.key = key
        self._attr_min_value = min_v
        self._attr_max_value = max_v

    @property
    def name(self):
        return f"SolMate {self.key}"

    @property
    def value(self):
        return self.coordinator.data.get(self.key)

    async def async_set_value(self, value: float):
        # TODO: WebSocket WRITE COMMAND
        await self.coordinator.ws.send({
            "set": self.key,
            "value": value
        })
