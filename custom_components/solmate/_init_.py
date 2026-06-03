async def async_setup_entry(hass, entry):
    from .coordinator import SolMateCoordinator

    host = entry.data["host"]
    port = entry.data["port"]

    coordinator = SolMateCoordinator(hass, host, port)
    entry.runtime_data = coordinator

    await coordinator.start()

    hass.data.setdefault("solmate", {})
    hass.data["solmate"][entry.entry_id] = coordinator

    return True
