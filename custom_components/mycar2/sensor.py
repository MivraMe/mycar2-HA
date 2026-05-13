from collections.abc import Callable
from dataclasses import dataclass, field

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricPotential, UnitOfSpeed, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import MyCar2Coordinator
from .entity import MyCar2Entity


@dataclass(frozen=True, kw_only=True)
class MyCar2SensorDescription(SensorEntityDescription):
    status_key: str = ""
    position_key: str = ""
    value_fn: Callable = field(default=lambda x: x)


def _mv_to_v(mv):
    return round(mv / 1000, 3) if mv is not None else None


SENSORS: tuple[MyCar2SensorDescription, ...] = (
    MyCar2SensorDescription(
        key="battery",
        translation_key="battery",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=2,
        status_key="BatteryVoltage",
        value_fn=_mv_to_v,
    ),
    MyCar2SensorDescription(
        key="gps_speed",
        translation_key="gps_speed",
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        suggested_display_precision=0,
        status_key="GpsSpeed",
    ),
    MyCar2SensorDescription(
        key="signal",
        translation_key="signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        suggested_display_precision=0,
        status_key="Rssi",
    ),
    MyCar2SensorDescription(
        key="interior_temperature",
        translation_key="interior_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="°C",
        suggested_display_precision=1,
        status_key="InteriorTemperature",
    ),
    MyCar2SensorDescription(
        key="firmware",
        translation_key="firmware",
        status_key="FWVersion",
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: MyCar2Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(MyCar2Sensor(coordinator, desc) for desc in SENSORS)


class MyCar2Sensor(MyCar2Entity, SensorEntity):
    entity_description: MyCar2SensorDescription

    def __init__(
        self, coordinator: MyCar2Coordinator, description: MyCar2SensorDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.vehicle_id}_{description.key}"

    @property
    def native_value(self):
        raw = self.coordinator.data.get("status", {}).get(self.entity_description.status_key)
        if raw is None:
            return None
        return self.entity_description.value_fn(raw)
