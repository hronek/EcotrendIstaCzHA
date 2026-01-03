"""Camera platform for ista EcoTrend CZ integration."""
from __future__ import annotations

import asyncio
import base64
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from .const import (
    COMPARISONS,
    CONF_ADDON_HOST,
    CONF_ADDON_PORT,
    CONF_CAMERAS,
    CONF_COMPARISON,
    CONF_INTERVAL,
    CONF_PASSWORD,
    CONF_TAB,
    CONF_THEME,
    CONF_UPDATE_INTERVAL,
    CONF_UPDATE_TIME,
    CONF_USERNAME,
    DEFAULT_ADDON_HOST,
    DEFAULT_ADDON_PORT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    INTERVALS,
    TABS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the EcoTrend camera platform."""
    cameras_config = entry.data.get(CONF_CAMERAS, [])
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    addon_host = entry.data.get(CONF_ADDON_HOST, DEFAULT_ADDON_HOST)
    addon_port = entry.data.get(CONF_ADDON_PORT, DEFAULT_ADDON_PORT)

    entities = []
    for idx, camera_config in enumerate(cameras_config):
        entities.append(
            EcotrendCamera(
                hass=hass,
                entry=entry,
                camera_config=camera_config,
                username=username,
                password=password,
                addon_host=addon_host,
                addon_port=addon_port,
                index=idx,
            )
        )

    async_add_entities(entities, True)


class EcotrendCamera(Camera):
    """Representation of an EcoTrend screenshot camera."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        camera_config: dict[str, Any],
        username: str,
        password: str,
        addon_host: str,
        addon_port: int,
        index: int,
    ) -> None:
        """Initialize the camera."""
        super().__init__()
        self.hass = hass
        self._entry = entry
        self._camera_config = camera_config
        self._username = username
        self._password = password
        self._addon_host = addon_host
        self._addon_port = addon_port
        self._index = index

        # Extract configuration
        self._tab = camera_config.get(CONF_TAB, "heat")
        self._interval = camera_config.get(CONF_INTERVAL, "months")
        self._comparison = camera_config.get(CONF_COMPARISON, "last_year")
        self._theme = camera_config.get(CONF_THEME, "auto")
        self._update_interval = camera_config.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        self._update_time = camera_config.get(CONF_UPDATE_TIME, "00:00")

        # Generate unique ID and name
        tab_name = TABS.get(self._tab, self._tab)
        interval_name = INTERVALS.get(self._interval, self._interval)
        comparison_name = COMPARISONS.get(self._comparison, self._comparison)

        self._attr_unique_id = f"{DOMAIN}_{self._tab}_{self._interval}_{self._comparison}_{index}"
        self._attr_name = f"EcoTrend {tab_name} {interval_name} {comparison_name}"

        # Image data
        self._image: bytes | None = None
        self._last_update: datetime | None = None
        self._is_updating = False

        # Unsub for scheduled updates
        self._unsub_time_change = None

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        # Register entity reference for service calls
        self.hass.data[DOMAIN].setdefault("entities", {})
        self.hass.data[DOMAIN]["entities"][self.entity_id] = self
        _LOGGER.debug("Registered entity %s for refresh service", self.entity_id)

        # Schedule update at specific time
        if self._update_time:
            try:
                hour, minute = map(int, self._update_time.split(":"))
                self._unsub_time_change = async_track_time_change(
                    self.hass,
                    self._scheduled_update,
                    hour=hour,
                    minute=minute,
                    second=0,
                )
                _LOGGER.info(
                    "Scheduled daily update for %s at %s:%s",
                    self._attr_name,
                    hour,
                    minute,
                )
            except ValueError:
                _LOGGER.error("Invalid update time format: %s", self._update_time)

        # Initial update - load screenshot immediately
        await self._async_update_image()

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        # Unregister entity reference
        if DOMAIN in self.hass.data and "entities" in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN]["entities"].pop(self.entity_id, None)

        if self._unsub_time_change:
            self._unsub_time_change()
            self._unsub_time_change = None

    async def _scheduled_update(self, now: datetime) -> None:
        """Handle scheduled update."""
        _LOGGER.info("Running scheduled update for %s", self._attr_name)
        await self._async_update_image()

    async def _async_update_image(self) -> None:
        """Update the camera image from the addon."""
        if self._is_updating:
            _LOGGER.debug("Update already in progress for %s", self._attr_name)
            return

        self._is_updating = True

        try:
            # Determine dark mode based on theme setting
            if self._theme == "auto":
                # Try to get HA theme, default to dark
                dark_mode = True  # Default to dark mode
                try:
                    # Check if HA has a theme set
                    if hasattr(self.hass, "data") and "frontend" in self.hass.data:
                        frontend_data = self.hass.data.get("frontend", {})
                        # This is a simplified check - actual implementation may vary
                        dark_mode = True
                except Exception:
                    pass
            else:
                dark_mode = self._theme == "dark"

            # Make request to addon
            url = f"http://{self._addon_host}:{int(self._addon_port)}/screenshot"
            payload = {
                "username": self._username,
                "password": self._password,
                "tab": self._tab,
                "interval": self._interval,
                "comparison": self._comparison,
                "dark_mode": dark_mode,
            }

            _LOGGER.debug("Requesting screenshot from addon: %s", url)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success") and data.get("image"):
                            self._image = base64.b64decode(data["image"])
                            self._last_update = dt_util.utcnow()
                            _LOGGER.info(
                                "Successfully updated image for %s",
                                self._attr_name,
                            )
                        else:
                            _LOGGER.error(
                                "Failed to get screenshot: %s",
                                data.get("error", "Unknown error"),
                            )
                    else:
                        _LOGGER.error(
                            "Addon returned status %s: %s",
                            response.status,
                            await response.text(),
                        )

        except aiohttp.ClientError as e:
            _LOGGER.error("Failed to connect to addon: %s", e)
        except Exception as e:
            _LOGGER.exception("Unexpected error updating camera image: %s", e)
        finally:
            self._is_updating = False

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return the camera image."""
        # Check if we need to update (based on interval)
        if self._image is None or (
            self._last_update
            and (dt_util.utcnow() - self._last_update)
            > timedelta(minutes=self._update_interval)
        ):
            await self._async_update_image()

        return self._image

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "tab": TABS.get(self._tab, self._tab),
            "interval": INTERVALS.get(self._interval, self._interval),
            "comparison": COMPARISONS.get(self._comparison, self._comparison),
            "theme": self._theme,
            "last_update": self._last_update.isoformat() if self._last_update else None,
            "update_interval_minutes": self._update_interval,
            "scheduled_update_time": self._update_time,
        }

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Ista EcoTrend CZ",
            "manufacturer": "Ista",
            "model": "EcoTrend CZ",
            "sw_version": "3.0.0",
        }

    async def async_update(self) -> None:
        """Update the camera (called by HA)."""
        # Don't auto-update too frequently - rely on scheduled updates
        pass
