from homeassistant.components.select import SelectEntity

OPTIONS = ["auto", "eco", "manual"]

async def async_setup_entry(hass, entry, async_add_entities):

    coordinator = hass.data["solmate"][entry.entry_id]

    async_add_entities([SolMateSelect(coordinator)])


class SolMateSelect(SelectEntity):

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "SolMate Mode"
        self._attr_unique_id = "solmate_mode"

    @property
    def options(self):
        return OPTIONS

    @property
    def current_option(self):
        return self.coordinator.data.get("mode")

    async def async_select_option(self, option):
        if self.coordinator.writer:
            await self.coordinator.writer.write("mode", option)
