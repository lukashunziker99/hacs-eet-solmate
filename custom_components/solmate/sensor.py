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
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

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


@dataclass(frozen=True, kw_only=True)
class SolMateEnergyDescription(SensorEntityDescription):
    """Energy meter integrated (Riemann/trapezoidal) from a power source in W."""

    power_fn: Callable          # (live dict) -> power in watts, or None
    requires_key: str           # only create if this live key exists


ENERGY_SENSORS: tuple[SolMateEnergyDescription, ...] = (
    SolMateEnergyDescription(
        key="pv_energy",
        name="PV energy",
        icon="mdi:solar-power",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        power_fn=lambda live: live.get("pv_power"),
        requires_key="pv_power",
    ),
    SolMateEnergyDescription(
        key="battery_charge_energy",
        name="Battery charge energy",
        icon="mdi:battery-plus-variant",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        power_fn=lambda live: _battery_charge(live.get("battery_flow")),
        requires_key="battery_flow",
    ),
    SolMateEnergyDescription(
        key="battery_discharge_energy",
        name="Battery discharge energy",
        icon="mdi:battery-minus-variant",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        power_fn=lambda live: _battery_discharge(live.get("battery_flow")),
        requires_key="battery_flow",
    ),
)


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

    # Add integrated energy (kWh) meters for the available power sources.
    for energy in ENERGY_SENSORS:
        if energy.requires_key in live:
            entities.append(SolMateEnergySensor(coordinator, energy))

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


class SolMateEnergySensor(SolMateBaseEntity, RestoreSensor):
    """Cumulative energy (kWh) integrated from a power source.

    Uses trapezoidal (Riemann) integration over each polling interval, like
    Home Assistant's own integration helper, but built straight into the
    integration. The running total is restored across restarts.
    """

    entity_description: SolMateEnergyDescription
    _attr_suggested_display_precision = 3

    def __init__(
        self, coordinator: SolMateCoordinator, description: SolMateEnergyDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self._serial}_{description.key}"
        self._total: float = 0.0
        self._last_power: float | None = None
        self._last_time = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_sensor_data()
        if last is not None and last.native_value is not None:
            try:
                self._total = float(last.native_value)
            except (TypeError, ValueError):
                self._total = 0.0
        # Establish the integration baseline from the current reading.
        live = (self.coordinator.data or {}).get("live", {})
        power = self.entity_description.power_fn(live)
        self._last_power = None if power is None else float(power)
        self._last_time = dt_util.utcnow()

    @callback
    def _handle_coordinator_update(self) -> None:
        live = (self.coordinator.data or {}).get("live", {})
        raw = self.entity_description.power_fn(live)
        power = None if raw is None else float(raw)
        now = dt_util.utcnow()

        if (
            power is not None
            and self._last_power is not None
            and self._last_time is not None
        ):
            dt_hours = (now - self._last_time).total_seconds() / 3600
            if dt_hours > 0:
                avg_watts = (power + self._last_power) / 2
                self._total += avg_watts * dt_hours / 1000.0

        self._last_power = power
        self._last_time = now
        super()._handle_coordinator_update()

    @property
    def native_value(self):
        return round(self._total, 3)

