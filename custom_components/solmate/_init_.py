from .const import DOMAIN
from .coordinator import SolMateCoordinator

async def async_setup_entry(hass, entry):
    host = entry.data["host"]
    port = entry.data["port"]

    coordinator = SolMateCoordinator(hass, host, port)

    await coordinator.start()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(
        entry,
        ["sensor", "number", "select", "switch"]
    )

    return True


async def async_unload_entry(hass, entry):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.stop()
    return True
