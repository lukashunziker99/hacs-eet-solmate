from homeassistant.components.number import NumberEntity

async def async_setup_entry(hass, entry, async_add_entities):

    coordinator = hass.data["solmate"][entry.entry_id]

    async_add_entities([
        SolMateNumber(coordinator)
    ])


class SolMateNumber(NumberEntity):

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "SolMate Battery Reserve"
        self._attr_unique_id = "solmate_battery_reserve"
        self._attr_min_value = 0
        self._attr_max_value = 100

    @property
    def value(self):
        return self.coordinator.data.get("battery_reserve")

    async def async_set_value(self, value: float):
        if self.coordinator.writer:
            await self.coordinator.writer.write(
                "battery_reserve",
                int(value)
            )
