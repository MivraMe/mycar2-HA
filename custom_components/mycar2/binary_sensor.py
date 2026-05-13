from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import MyCar2Coordinator
from .entity import MyCar2Entity


@dataclass(frozen=True, kw_only=True)
class MyCar2BinarySensorDescription(BinarySensorEntityDescription):
    status_key: str = ""
    # Set True when the API field meaning is the logical opposite of the HA device class.
    # e.g. IsOffline=True → CONNECTIVITY should report off (disconnected).
    invert: bool = False


SENSORS: tuple[MyCar2BinarySensorDescription, ...] = (
    MyCar2BinarySensorDescription(
        key="engine",
        translation_key="engine",
        device_class=BinarySensorDeviceClass.RUNNING,
        status_key="Status_Engine",
    ),
    MyCar2BinarySensorDescription(
        key="ignition",
        translation_key="ignition",
        device_class=BinarySensorDeviceClass.POWER,
        status_key="Status_Ignition",
    ),
    MyCar2BinarySensorDescription(
        key="trunk",
        translation_key="trunk",
        device_class=BinarySensorDeviceClass.OPENING,
        status_key="Status_Trunk",
    ),
    MyCar2BinarySensorDescription(
        key="hood",
        translation_key="hood",
        device_class=BinarySensorDeviceClass.OPENING,
        status_key="Status_Hood",
    ),
    MyCar2BinarySensorDescription(
        key="doors",
        translation_key="doors_open",
        device_class=BinarySensorDeviceClass.DOOR,
        status_key="Status_Doors",
    ),
    MyCar2BinarySensorDescription(
        key="offline",
        translation_key="offline",
        # CONNECTIVITY: on=Connected, off=Disconnected.
        # IsOffline=True means the device is offline → invert so is_on=False → "Disconnected".
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        status_key="IsOffline",
        invert=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: MyCar2Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(MyCar2BinarySensor(coordinator, desc) for desc in SENSORS)


class MyCar2BinarySensor(MyCar2Entity, BinarySensorEntity):
    entity_description: MyCar2BinarySensorDescription

    def __init__(
        self, coordinator: MyCar2Coordinator, description: MyCar2BinarySensorDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.vehicle_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        raw = self.coordinator.data.get("status", {}).get(self.entity_description.status_key)
        if raw is None:
            return None
        value = bool(raw)
        return (not value) if self.entity_description.invert else value
