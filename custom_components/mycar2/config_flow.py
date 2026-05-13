import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AuthenticationError, MyCar2ApiClient
from .const import CONF_VEHICLE_ID, CONF_VEHICLE_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


class MyCar2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._api: MyCar2ApiClient | None = None
        self._vehicles: list = []
        self._username: str = ""
        self._password: str = ""

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = MyCar2ApiClient(session, user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
            try:
                await api.authenticate()
                self._vehicles = await api.get_vehicles()
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected error during setup")
                errors["base"] = "cannot_connect"
            else:
                self._api = api
                self._username = user_input[CONF_USERNAME]
                self._password = user_input[CONF_PASSWORD]
                if len(self._vehicles) == 1:
                    return self._create_entry(self._vehicles[0])
                return await self.async_step_vehicle()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )

    async def async_step_vehicle(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            vehicle_id = user_input[CONF_VEHICLE_ID]
            vehicle = next((v for v in self._vehicles if v.get("Id") == vehicle_id), None)
            if vehicle:
                return self._create_entry(vehicle)
            errors["base"] = "unknown"

        vehicles_map = {
            v["Id"]: _vehicle_label(v)
            for v in self._vehicles
        }
        return self.async_show_form(
            step_id="vehicle",
            data_schema=vol.Schema({
                vol.Required(CONF_VEHICLE_ID): vol.In(vehicles_map),
            }),
            errors=errors,
        )

    def _create_entry(self, vehicle: dict):
        vehicle_id = vehicle["Id"]
        vehicle_name = vehicle.get("Name", vehicle_id)
        return self.async_create_entry(
            title=vehicle_name,
            data={
                CONF_USERNAME: self._username,
                CONF_PASSWORD: self._password,
                CONF_VEHICLE_ID: vehicle_id,
                CONF_VEHICLE_NAME: vehicle_name,
            },
        )


def _vehicle_label(vehicle: dict) -> str:
    img = vehicle.get("VehicleImageInfo", {})
    parts = [
        vehicle.get("Name", ""),
        img.get("Year", ""),
        img.get("Make", ""),
        img.get("Model", ""),
    ]
    return " ".join(p for p in parts if p).strip() or vehicle["Id"]
