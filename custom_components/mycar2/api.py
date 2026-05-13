import asyncio
import logging
from datetime import datetime, timedelta

import aiohttp

from .const import API_BASE_URL, CMD_AWAKE, COGNITO_CLIENT_ID, COGNITO_ENDPOINT, TOKEN_REFRESH_INTERVAL

_LOGGER = logging.getLogger(__name__)


class AuthenticationError(Exception):
    pass


class MyCar2ApiClient:
    def __init__(self, session: aiohttp.ClientSession, username: str, password: str) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._id_token: str | None = None
        self._refresh_token: str | None = None
        self._token_acquired_at: datetime | None = None
        self._refresh_lock = asyncio.Lock()

    @property
    def id_token(self) -> str | None:
        return self._id_token

    async def authenticate(self) -> None:
        payload = {
            "AuthFlow": "USER_PASSWORD_AUTH",
            "ClientId": COGNITO_CLIENT_ID,
            "AuthParameters": {
                "USERNAME": self._username,
                "PASSWORD": self._password,
            },
        }
        headers = {
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "Content-Type": "application/x-amz-json-1.1",
        }
        async with self._session.post(COGNITO_ENDPOINT, json=payload, headers=headers) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise AuthenticationError(f"Login failed ({resp.status}): {text}")
            data = await resp.json(content_type=None)

        auth = data.get("AuthenticationResult", {})
        self._id_token = auth["IdToken"]
        self._refresh_token = auth["RefreshToken"]
        self._token_acquired_at = datetime.utcnow()
        _LOGGER.debug("Authenticated successfully")

    async def ensure_token(self) -> None:
        if self._token_acquired_at is None:
            await self.authenticate()
            return
        elapsed = (datetime.utcnow() - self._token_acquired_at).total_seconds()
        if elapsed >= TOKEN_REFRESH_INTERVAL:
            async with self._refresh_lock:
                # Re-check inside the lock
                elapsed = (datetime.utcnow() - self._token_acquired_at).total_seconds()
                if elapsed >= TOKEN_REFRESH_INTERVAL:
                    await self._do_refresh()

    async def _do_refresh(self) -> None:
        payload = {
            "AuthFlow": "REFRESH_TOKEN_AUTH",
            "ClientId": COGNITO_CLIENT_ID,
            "AuthParameters": {"REFRESH_TOKEN": self._refresh_token},
        }
        headers = {
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "Content-Type": "application/x-amz-json-1.1",
        }
        try:
            async with self._session.post(COGNITO_ENDPOINT, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    _LOGGER.warning("Token refresh failed (%s), re-authenticating", resp.status)
                    await self.authenticate()
                    return
                data = await resp.json(content_type=None)
            auth = data.get("AuthenticationResult", {})
            self._id_token = auth["IdToken"]
            self._token_acquired_at = datetime.utcnow()
            _LOGGER.debug("Token refreshed")
        except Exception as err:
            _LOGGER.warning("Token refresh error (%s), re-authenticating", err)
            await self.authenticate()

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._id_token}"}

    async def get_vehicles(self) -> list:
        await self.ensure_token()
        url = f"{API_BASE_URL}/CarstarterService/GetAllVehicles/MyCar2?lang=fr"
        async with self._session.get(url, headers=self._auth_headers()) as resp:
            resp.raise_for_status()
            return await resp.json(content_type=None)

    async def get_vehicle_position(self, vehicle_id: str) -> dict:
        await self.ensure_token()
        url = f"{API_BASE_URL}/CarstarterService/GetLastVehiclePosition/{vehicle_id}"
        async with self._session.get(url, headers=self._auth_headers()) as resp:
            resp.raise_for_status()
            return await resp.json(content_type=None)

    async def get_vehicle_status(self, vehicle_id: str) -> dict:
        await self.ensure_token()
        url = f"{API_BASE_URL}/CarstarterService/GetLastVehicleStatus/{vehicle_id}"
        async with self._session.get(url, headers=self._auth_headers()) as resp:
            resp.raise_for_status()
            return await resp.json(content_type=None)

    async def send_command(self, vehicle_id: str, command: int) -> dict:
        await self.ensure_token()
        url = f"{API_BASE_URL}/CarstarterService/SendCarCommand"
        payload = {"VehicleId": vehicle_id, "CarCommand": command}
        async with self._session.post(url, json=payload, headers=self._auth_headers()) as resp:
            resp.raise_for_status()
            return await resp.json(content_type=None)

    async def awake_and_command(self, vehicle_id: str, command: int, status: dict | None = None) -> dict:
        """Wake the device if offline before sending a command."""
        if status and status.get("IsOffline"):
            _LOGGER.debug("Device offline, sending awake first")
            try:
                await self.send_command(vehicle_id, CMD_AWAKE)
                await asyncio.sleep(2)
            except Exception as err:
                _LOGGER.warning("Awake command failed: %s", err)
        return await self.send_command(vehicle_id, command)
