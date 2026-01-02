"""Constants for the Ista EcoTrend CZ integration."""

DOMAIN = "ecotrend_ista_cz"

# Default values
DEFAULT_URL = "https://ecotrend.ista.cz/"
DEFAULT_NAME = "Ista EcoTrend CZ"
DEFAULT_ADDON_HOST = "localhost"
DEFAULT_ADDON_PORT = 5000
DEFAULT_UPDATE_INTERVAL = 1440  # minutes (24 hours)
DEFAULT_UPDATE_TIME = "00:00"

# Configuration keys
CONF_URL = "url"
CONF_PANEL_TITLE = "panel_title"
CONF_PANEL_ICON = "panel_icon"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_ADDON_HOST = "addon_host"
CONF_ADDON_PORT = "addon_port"
CONF_CAMERAS = "cameras"
CONF_TAB = "tab"
CONF_INTERVAL = "interval"
CONF_COMPARISON = "comparison"
CONF_DARK_MODE = "dark_mode"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_UPDATE_TIME = "update_time"
CONF_THEME = "theme"

# Default icon for the panel
DEFAULT_ICON = "mdi:water-thermometer"

# Available tabs
TABS = {
    "heat": "Teplo",
    "hot_water": "Teplá voda",
    "cold_water": "Studená voda",
}

# Available intervals
INTERVALS = {
    "days": "Dny",
    "weeks": "Týdny",
    "months": "Měsíce",
    "years": "Roky",
}

# Available comparisons
COMPARISONS = {
    "object": "Objekt",
    "last_year": "Minulý rok",
}

# Valid combinations (tab -> available comparisons)
# Studená voda doesn't have "Objekt" option
VALID_COMPARISONS = {
    "heat": ["object", "last_year"],
    "hot_water": ["object", "last_year"],
    "cold_water": ["last_year"],
}

# Theme options
THEMES = {
    "auto": "Automaticky (dle HA)",
    "dark": "Tmavé",
    "light": "Světlé",
}

# Platforms
PLATFORMS = ["camera"]
