"""The Ista EcoTrend CZ integration."""
from __future__ import annotations

import logging

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    CONF_PANEL_ICON,
    CONF_PANEL_TITLE,
    CONF_URL,
    DEFAULT_ICON,
    DEFAULT_NAME,
    DEFAULT_URL,
    DOMAIN,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)

SERVICE_REFRESH_SCREENSHOT = "refresh_screenshot"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ista EcoTrend CZ from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data
    hass.data[DOMAIN].setdefault("entities", {})

    url = entry.data.get(CONF_URL, DEFAULT_URL)
    title = entry.data.get(CONF_PANEL_TITLE, DEFAULT_NAME)
    icon = entry.data.get(CONF_PANEL_ICON, DEFAULT_ICON)

    # Register the iframe panel for direct access to EcoTrend
    try:
        async_register_built_in_panel(
            hass,
            component_name="iframe",
            sidebar_title=title,
            sidebar_icon=icon,
            frontend_url_path=DOMAIN,
            config={"url": url},
            require_admin=False,
        )
        _LOGGER.info("Ista EcoTrend CZ panel registered: %s", url)
    except Exception as e:
        _LOGGER.warning("Could not register panel (may already exist): %s", e)

    # Set up platforms (camera)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register service for manual screenshot refresh
    async def handle_refresh_screenshot(call: ServiceCall) -> None:
        """Handle the refresh_screenshot service call."""
        entity_id = call.data.get("entity_id")

        if not entity_id:
            _LOGGER.error("No entity_id provided for refresh_screenshot service")
            return

        # Get the camera entity from our stored references
        entities = hass.data.get(DOMAIN, {}).get("entities", {})
        entity = entities.get(entity_id)

        if entity and hasattr(entity, "_async_update_image"):
            _LOGGER.info("Refreshing screenshot for %s", entity_id)
            try:
                await entity._async_update_image()
                _LOGGER.info("Screenshot refresh completed for %s", entity_id)
            except Exception as e:
                _LOGGER.error("Failed to refresh screenshot for %s: %s", entity_id, e)
        else:
            _LOGGER.error("Entity %s not found or does not support refresh. Available: %s", entity_id, list(entities.keys()))

    hass.services.async_register(DOMAIN, SERVICE_REFRESH_SCREENSHOT, handle_refresh_screenshot)

    # Register update listener for options
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Remove service
        hass.services.async_remove(DOMAIN, SERVICE_REFRESH_SCREENSHOT)

        # Remove the panel
        try:
            hass.components.frontend.async_remove_panel(DOMAIN)
        except Exception as e:
            _LOGGER.warning("Could not remove panel: %s", e)

        hass.data[DOMAIN].pop(entry.entry_id, None)

        _LOGGER.info("Ista EcoTrend CZ integration unloaded")

    return unload_ok
