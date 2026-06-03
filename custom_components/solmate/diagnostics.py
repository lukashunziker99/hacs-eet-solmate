async def async_get_config_entry_diagnostics(hass, entry):

    coordinator = hass.data["solmate"][entry.entry_id]

    return {
        "host": entry.data["host"],
        "data_keys": list(coordinator.data.keys()),
        "last_values": coordinator.data,
    }
