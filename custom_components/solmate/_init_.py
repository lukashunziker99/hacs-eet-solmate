async def async_setup_entry(hass, entry):

    coordinator = SolMateCoordinator(
        hass,
        entry.data["host"],
        entry.data["port"]
    )

    await coordinator.start()

    hass.data.setdefault("solmate", {})
    hass.data["solmate"][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(
        entry,
        ["sensor", "number", "select", "switch"]
    )

    return True


async def async_unload_entry(hass, entry):

    coordinator = hass.data["solmate"][entry.entry_id]
    await coordinator.stop()

    return True
