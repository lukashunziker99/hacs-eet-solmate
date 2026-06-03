from homeassistant.components.select import SelectEntity

OPTIONS = ["auto", "eco", "force_charge"]

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data

    async_add_entities([
        SolMateSelect(coordinator, "mode")
    ])

class SolMateSelect(SelectEntity):
    @property
    def options(self):
        return OPTIONS

    @property
    def current_option(self):
        return self.coordinator.data.get("mode")

    async def async_select_option(self, option):
        await self.coordinator.ws.send({
            "set_mode": option
        })
