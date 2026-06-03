from .coordinator import SolMateCoordinator

DOMAIN = "solmate"

async def async_setup_entry(hass, entry):
    host = entry.data["host"]
    port = entry.data["port"]

    coordinator = SolMateCoordinator(hass, host, port)
    await coordinator.start()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    hass.config_entries.async_setup_platforms(entry, ["sensor", "number", "select", "switch"])

    return True


async def async_unload_entry(hass, entry):
    return True
