from homeassistant.components.switch import SwitchEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data

    async_add_entities([
        SolMateSwitch(coordinator, "force_charge")
    ])

class SolMateSwitch(SwitchEntity):
    @property
    def is_on(self):
        return self.coordinator.data.get(self.key)

    async def async_turn_on(self):
        await self.coordinator.ws.send({"force_charge": True})

    async def async_turn_off(self):
        await self.coordinator.ws.send({"force_charge": False})
