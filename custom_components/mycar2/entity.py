from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MyCar2Coordinator


class MyCar2Entity(CoordinatorEntity[MyCar2Coordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: MyCar2Coordinator) -> None:
        super().__init__(coordinator)
        info = coordinator.vehicle_info
        img = info.get("VehicleImageInfo", {})
        model = " ".join(filter(None, [img.get("Year"), img.get("Model"), img.get("Trim")])).strip()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.vehicle_id)},
            name=info.get("Name", coordinator.vehicle_id),
            manufacturer=img.get("Make", "MyCar2"),
            model=model or None,
        )
