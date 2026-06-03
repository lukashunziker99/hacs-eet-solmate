async def async_get_config_entry_diagnostics(hass, entry):

    coordinator = hass.data["solmate"][entry.entry_id]

    return {
        "host": entry.data["host"],
        "port": entry.data["port"],
        "data": coordinator.data,
        "entity_count": len(coordinator.data),
    }
