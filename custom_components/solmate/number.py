"""Number platform for the EET SolMate integration (writable controls)."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntityDescription,
    NumberMode,
    RestoreNumber,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import SolMateClient
from .const import DOMAIN
from .coordinator import SolMateCoordinator
from .entity import SolMateBaseEntity


@dataclass(frozen=True, kw_only=True)
class SolMateNumberDescription(NumberEntityDescription):
    """Number description with a writer and candidate read-back keys."""

    set_fn: Callable[[SolMateClient, float], Awaitable]
    source: str = "injection"          # which settings dict to read the current value from
    value_keys: tuple[str, ...] = ()   # candidate keys for the current value


NUMBERS: tuple[SolMateNumberDescription, ...] = (
    SolMateNumberDescription(
        key="min_injection",
        name="Minimum injection",
        icon="mdi:transmission-tower-export",
        native_unit_of_measurement=UnitOfPower.WATT,
        native_min_value=0,
        native_max_value=1000,
        native_step=5,
        mode=NumberMode.BOX,
        set_fn=lambda client, value: client.set_min_injection(value),
        source="injection",
        value_keys=("user_minimum_injection", "minimum_injection", "min_injection"),
    ),
    SolMateNumberDescription(
        key="max_injection",
        name="Maximum injection",
        icon="mdi:transmission-tower-export",
        native_unit_of_measurement=UnitOfPower.WATT,
        native_min_value=0,
        native_max_value=1000,
        native_step=5,
        mode=NumberMode.BOX,
        set_fn=lambda client, value: client.set_max_injection(value),
        source="injection",
        value_keys=("user_maximum_injection", "maximum_injection", "max_injection"),
    ),
    SolMateNumberDescription(
        key="min_battery",
        name="Minimum battery",
        icon="mdi:battery-low",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        set_fn=lambda client, value: client.set_min_battery_percentage(value),
        source="user",
        value_keys=(
            "user_minimum_battery_percentage",
            "minimum_battery_percentage",
            "min_battery_percentage",
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SolMateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(SolMateNumber(coordinator, desc) for desc in NUMBERS)


class SolMateNumber(SolMateBaseEntity, RestoreNumber):
    """A writable SolMate setting."""

    entity_description: SolMateNumberDescription

    def __init__(
        self, coordinator: SolMateCoordinator, description: SolMateNumberDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self._serial}_{description.key}"
        self._restored: float | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_number_data()
        if last is not None and last.native_value is not None:
            self._restored = last.native_value

    @property
    def native_value(self):
        # Prefer a value reported by the device; fall back to the last value we set.
        settings = (self.coordinator.data or {}).get(self.entity_description.source, {})
        for key in self.entity_description.value_keys:
            if isinstance(settings, dict) and settings.get(key) is not None:
                return settings[key]
        return self._restored

    async def async_set_native_value(self, value: float) -> None:
        await self.entity_description.set_fn(self.coordinator.client, value)
        self._restored = value
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
