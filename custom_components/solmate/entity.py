"""Shared entity base for the EET SolMate integration."""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SERIAL, DOMAIN
from .coordinator import SolMateCoordinator


class SolMateBaseEntity(CoordinatorEntity[SolMateCoordinator]):
    """Base entity that wires device info and coordinator updates."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SolMateCoordinator) -> None:
        super().__init__(coordinator)
        self._serial = coordinator.entry.data[CONF_SERIAL]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._serial)},
            name=f"EET SolMate {self._serial}",
            manufacturer="EET - Efficient Energy Technology",
            model="SolMate",
        )
