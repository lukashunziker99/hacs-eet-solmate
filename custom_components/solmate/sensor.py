"""Sensor platform for the EET SolMate integration.

Sensors are created dynamically from the keys returned by ``live_values`` so
the integration adapts to whatever the device firmware actually reports. Known
keys get nice units / device classes; unknown keys still show up as plain
measurement sensors.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SolMateCoordinator
from .entity import SolMateBaseEntity


def _battery_scale(value):
    """SolMate reports SOC as a 0..1 fraction or a 0..100 percent (firmware dependent)."""
    if value is None:
        return None
    try:
        return round(value * 100, 1) if value <= 1 else round(value, 1)
    except TypeError:
        return value


# SolMate sign convention (verified against the mmattel/EET-Solmate project):
#   battery_flow < 0  -> charging
#   battery_flow > 0  -> discharging
# If your firmware turns out to be inverted, just swap the two functions below.
def _battery_charge(flow):
    """Charging power as a positive value (0 while discharging)."""
    if flow is None:
        return None
    try:
        return max(0.0, -float(flow))
    except (TypeError, ValueError):
        return None


def _battery_discharge(flow):
    """Discharging power as a positive value (0 while charging)."""
    if flow is None:
        return None
    try:
        return max(0.0, float(flow))
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True, kw_only=True)
class SolMateSensorDescription(SensorEntityDescription):
    """Sensor description with an optional value transform / computation."""

    value_fn: Callable = field(default=lambda v: v)
    # When set, the value is computed from the full live dict instead of a single key.
    compute: Callable | None = None


KNOWN_SENSORS: dict[str, SolMateSensorDescription] = {
    "pv_power": SolMateSensorDescription(
        key="pv_power",
        name="PV power",
        icon="mdi:solar-power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "inject_power": SolMateSensorDescription(
        key="inject_power",
        name="Injection power",
        icon="mdi:transmission-tower-export",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "battery_flow": SolMateSensorDescription(
        key="battery_flow",
        name="Battery flow",
        icon="mdi:battery-charging",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "battery_state": SolMateSensorDescription(
        key="battery_state",
        name="Battery",
        icon="mdi:battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_battery_scale,
    ),
}

# Sensors derived from battery_flow (only added if battery_flow is reported).
COMPUTED_SENSORS: tuple[SolMateSensorDescription, ...] = (
    SolMateSensorDescription(
        key="battery_charge",
        name="Battery charge",
        icon="mdi:battery-plus-variant",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        compute=lambda live: _battery_charge(live.get("battery_flow")),
    ),
    SolMateSensorDescription(
        key="battery_discharge",
        name="Battery discharge",
        icon="mdi:battery-minus-variant",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        compute=lambda live: _battery_discharge(live.get("battery_flow")),
    ),
)

# Keys we never want as their own sensor entity.
SKIP_KEYS = {"timestamp"}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SolMateCoordinator = hass.data[DOMAIN][entry.entry_id]
    live = (coordinator.data or {}).get("live", {})

    entities: list[SolMateSensor] = []
    for key, value in live.items():
        if key in SKIP_KEYS:
            continue
        description = KNOWN_SENSORS.get(key) or SolMateSensorDescription(
            key=key,
            name=key.replace("_", " ").capitalize(),
            state_class=(
                SensorStateClass.MEASUREMENT
                if isinstance(value, (int, float)) and not isinstance(value, bool)
                else None
            ),
        )
        entities.append(SolMateSensor(coordinator, description))

    # Add derived charge / discharge sensors if the device reports battery_flow.
    if "battery_flow" in live:
        for description in COMPUTED_SENSORS:
            entities.append(SolMateSensor(coordinator, description))

    async_add_entities(entities)


class SolMateSensor(SolMateBaseEntity, SensorEntity):
    """A single live value from the SolMate."""

    entity_description: SolMateSensorDescription

    def __init__(
        self, coordinator: SolMateCoordinator, description: SolMateSensorDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self._serial}_{description.key}"

    @property
    def native_value(self):
        live = (self.coordinator.data or {}).get("live", {})
        if self.entity_description.compute is not None:
            return self.entity_description.compute(live)
        return self.entity_description.value_fn(live.get(self.entity_description.key))
