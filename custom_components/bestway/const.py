"""Constants for the Bestway integration."""

from datetime import timedelta

DOMAIN = "bestway"
PLATFORMS = ["climate", "switch", "sensor", "binary_sensor"]

CONF_REGION = "region"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

DEFAULT_REGION = "euapi"
API_REGIONS = ["euapi", "usapi", "aaapi"]

APP_ID = "98754e684ec045528b073876c34c7348"
APP_KEY_V2 = "43424551921d4ee18dd279140e11e198"
CONTROL_V2_URL = "https://euaepapp.gizwits.com/app/user/control_log"

POLL_INTERVAL = timedelta(minutes=10)
TOKEN_REFRESH_INTERVAL = timedelta(days=7)
