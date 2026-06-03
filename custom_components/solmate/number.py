from homeassistant.components.number import NumberEntity

class SolMateNumber(NumberEntity):

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "SolMate Battery Reserve"
        self._attr_unique_id = "solmate_battery_reserve"

    @property
    def value(self):
        return self.coordinator.data.get("battery_reserve")

    async def async_set_value(self, value):
        if self.coordinator.writer:
            await self.coordinator.writer.write(
                self.coordinator,
                "battery_reserve",
                int(value)
            )
