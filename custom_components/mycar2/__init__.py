import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AuthenticationError, MyCar2ApiClient
from .const import CONF_VEHICLE_ID, DOMAIN, PLATFORMS
from .coordinator import MyCar2Coordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    api = MyCar2ApiClient(
        session,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )

    try:
        await api.authenticate()
    except AuthenticationError as err:
        _LOGGER.error("Authentication failed: %s", err)
        return False

    vehicles = await api.get_vehicles()
    vehicle_id = entry.data[CONF_VEHICLE_ID]
    vehicle_info = next((v for v in vehicles if v.get("Id") == vehicle_id), {})

    coordinator = MyCar2Coordinator(hass, api, vehicle_id, vehicle_info)
    await coordinator.async_config_entry_first_refresh()
    coordinator.start_background_tasks()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        coordinator: MyCar2Coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator.stop_background_tasks()
    return unloaded
