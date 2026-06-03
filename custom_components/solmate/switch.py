from homeassistant.components.switch import SwitchEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data["solmate"][entry.entry_id]

    async_add_entities([
        SolMateSwitch(coordinator)
    ])

class SolMateSwitch(SwitchEntity):
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "SolMate Force Charge"
        self._attr_unique_id = "solmate_force_charge"

    @property
    def is_on(self):
        return self.coordinator.data.get("force_charge")

    async def async_turn_on(self):
        # TODO WRITE COMMAND
        pass

    async def async_turn_off(self):
        # TODO WRITE COMMAND
        pass
