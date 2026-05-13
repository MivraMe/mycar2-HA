from homeassistant.const import Platform

DOMAIN = "mycar2"

COGNITO_ENDPOINT = "https://cognito-idp.us-east-1.amazonaws.com/"
COGNITO_CLIENT_ID = "3t704g14i0l52mfkt77ldaoshp"

API_BASE_URL = "https://api.mybrandedapp.com"

PLATFORMS = [
    Platform.LOCK,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.DEVICE_TRACKER,
]

# CarCommand values
CMD_LOCK = 0
CMD_UNLOCK = 1
CMD_TRUNK = 2
CMD_START = 3
CMD_STOP = 4
CMD_EXTEND = 5
CMD_PANIC_ON = 6
CMD_PANIC_OFF = 7
CMD_AWAKE = 9
CMD_VALET = 20
CMD_REFRESH_RS = 21

# Token refresh: 55 min (Cognito tokens expire at 1 h)
TOKEN_REFRESH_INTERVAL = 55 * 60
POLL_INTERVAL = 30
KEYFOB_SYNC_INTERVAL = 5 * 60

CONF_VEHICLE_ID = "vehicle_id"
CONF_VEHICLE_NAME = "vehicle_name"
