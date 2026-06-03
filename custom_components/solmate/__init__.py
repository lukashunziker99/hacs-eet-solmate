print("SOLMATE IMPORT OK")
from .const import DOMAIN
from .coordinator import SolMateCoordinator


async def async_setup_entry(hass, entry):
    """Set up SolMate from a config entry."""

    coordinator = SolMateCoordinator(
        hass,
        entry.data["host"],
        entry.data["port"]
    )

    # Store coordinator early (important for unload + future access)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # IMPORTANT:
    # Do NOT block setup with network IO / websocket start
    # Run it in background task instead
    hass.async_create_task(coordinator.start())

    # Forward platforms
    await hass.config_entries.async_forward_entry_setups(
        entry,
        ["sensor", "number", "select", "switch"]
    )

    return True


async def async_unload_entry(hass, entry):
    """Unload SolMate config entry."""

    coordinator = hass.data[DOMAIN].get(entry.entry_id)

    if coordinator:
        await coordinator.stop()

    hass.data[DOMAIN].pop(entry.entry_id, None)

    return True
