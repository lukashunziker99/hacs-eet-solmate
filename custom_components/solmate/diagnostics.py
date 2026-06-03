async def async_get_config_entry_diagnostics(hass, entry):

    coordinator = hass.data["solmate"][entry.entry_id]

    return {
        "host": entry.data["host"],
        "port": entry.data["port"],
        "entities": list(coordinator.data.keys()),
        "snapshot": coordinator.data,
        "ws_connected": coordinator.ws_client.ws is not None if hasattr(coordinator, "ws_client") else False
    }
