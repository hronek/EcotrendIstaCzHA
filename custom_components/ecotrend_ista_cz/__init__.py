"""The ista EcoTrend CZ integration."""
from __future__ import annotations

import logging

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_PANEL_ICON,
    CONF_PANEL_TITLE,
    CONF_URL,
    DEFAULT_ICON,
    DEFAULT_NAME,
    DEFAULT_URL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ista EcoTrend CZ from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    url = entry.data.get(CONF_URL, DEFAULT_URL)
    title = entry.data.get(CONF_PANEL_TITLE, DEFAULT_NAME)
    icon = entry.data.get(CONF_PANEL_ICON, DEFAULT_ICON)

    # Register the iframe panel
    async_register_built_in_panel(
        hass,
        component_name="iframe",
        sidebar_title=title,
        sidebar_icon=icon,
        frontend_url_path=DOMAIN,
        config={"url": url},
        require_admin=False,
    )

    _LOGGER.info("ista EcoTrend CZ panel registered: %s", url)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Remove the panel
    if DOMAIN in hass.data.get("frontend_panels", {}):
        hass.components.frontend.async_remove_panel(DOMAIN)

    hass.data[DOMAIN].pop(entry.entry_id)

    _LOGGER.info("ista EcoTrend CZ panel unloaded")

    return True
