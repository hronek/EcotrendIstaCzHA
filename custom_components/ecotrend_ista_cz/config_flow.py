"""Config flow for ista EcoTrend CZ integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
    TimeSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    BooleanSelector,
)

from .const import (
    COMPARISONS,
    CONF_ADDON_HOST,
    CONF_ADDON_PORT,
    CONF_CAMERAS,
    CONF_COMPARISON,
    CONF_DARK_MODE,
    CONF_INTERVAL,
    CONF_PANEL_ICON,
    CONF_PANEL_TITLE,
    CONF_PASSWORD,
    CONF_TAB,
    CONF_THEME,
    CONF_UPDATE_INTERVAL,
    CONF_UPDATE_TIME,
    CONF_URL,
    CONF_USERNAME,
    DEFAULT_ADDON_HOST,
    DEFAULT_ADDON_PORT,
    DEFAULT_ICON,
    DEFAULT_NAME,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_UPDATE_TIME,
    DEFAULT_URL,
    DOMAIN,
    INTERVALS,
    TABS,
    THEMES,
    VALID_COMPARISONS,
)

_LOGGER = logging.getLogger(__name__)


async def validate_addon_connection(host: str, port: int) -> bool:
    """Validate connection to the screenshot addon."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"http://{host}:{port}/health"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
    except Exception as e:
        _LOGGER.warning("Could not connect to addon: %s", e)
        return False


class EcotrendIstaCzConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ista EcoTrend CZ."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}
        self._cameras: list[dict[str, str]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step - credentials and addon settings."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            # Validate addon connection
            addon_host = user_input.get(CONF_ADDON_HOST, DEFAULT_ADDON_HOST)
            addon_port = user_input.get(CONF_ADDON_PORT, DEFAULT_ADDON_PORT)

            if not await validate_addon_connection(addon_host, addon_port):
                errors["base"] = "addon_not_available"
            else:
                self._data = user_input
                return await self.async_step_cameras()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.TEXT)
                    ),
                    vol.Required(CONF_PASSWORD): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                    vol.Optional(CONF_ADDON_HOST, default=DEFAULT_ADDON_HOST): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.TEXT)
                    ),
                    vol.Optional(CONF_ADDON_PORT, default=DEFAULT_ADDON_PORT): NumberSelector(
                        NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX)
                    ),
                    vol.Optional(CONF_PANEL_TITLE, default=DEFAULT_NAME): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.TEXT)
                    ),
                    vol.Optional(CONF_PANEL_ICON, default=DEFAULT_ICON): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.TEXT)
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_cameras(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle adding cameras step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            tab = user_input.get(CONF_TAB)
            interval = user_input.get(CONF_INTERVAL)
            comparison = user_input.get(CONF_COMPARISON)
            theme = user_input.get(CONF_THEME, "auto")
            update_interval = user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
            update_time = user_input.get(CONF_UPDATE_TIME, DEFAULT_UPDATE_TIME)

            # Validate comparison is valid for tab
            if comparison not in VALID_COMPARISONS.get(tab, []):
                errors["base"] = "invalid_comparison"
            else:
                camera_config = {
                    CONF_TAB: tab,
                    CONF_INTERVAL: interval,
                    CONF_COMPARISON: comparison,
                    CONF_THEME: theme,
                    CONF_UPDATE_INTERVAL: update_interval,
                    CONF_UPDATE_TIME: update_time,
                }
                self._cameras.append(camera_config)

                # Ask if user wants to add more cameras
                return await self.async_step_add_more()

        # Build comparison options based on selected tab (default to heat)
        comparison_options = [
            {"value": k, "label": v}
            for k, v in COMPARISONS.items()
        ]

        return self.async_show_form(
            step_id="cameras",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TAB): SelectSelector(
                        SelectSelectorConfig(
                            options=[{"value": k, "label": v} for k, v in TABS.items()],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_INTERVAL): SelectSelector(
                        SelectSelectorConfig(
                            options=[{"value": k, "label": v} for k, v in INTERVALS.items()],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_COMPARISON): SelectSelector(
                        SelectSelectorConfig(
                            options=comparison_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(CONF_THEME, default="auto"): SelectSelector(
                        SelectSelectorConfig(
                            options=[{"value": k, "label": v} for k, v in THEMES.items()],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): NumberSelector(
                        NumberSelectorConfig(min=60, max=10080, step=60, mode=NumberSelectorMode.BOX, unit_of_measurement="min")
                    ),
                    vol.Optional(CONF_UPDATE_TIME, default=DEFAULT_UPDATE_TIME): TimeSelector(),
                }
            ),
            errors=errors,
            description_placeholders={
                "camera_count": str(len(self._cameras)),
            },
        )

    async def async_step_add_more(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask if user wants to add more cameras."""
        if user_input is not None:
            if user_input.get("add_another"):
                return await self.async_step_cameras()
            else:
                # Finish configuration
                self._data[CONF_CAMERAS] = self._cameras
                self._data[CONF_URL] = DEFAULT_URL

                return self.async_create_entry(
                    title=self._data.get(CONF_PANEL_TITLE, DEFAULT_NAME),
                    data=self._data,
                )

        return self.async_show_form(
            step_id="add_more",
            data_schema=vol.Schema(
                {
                    vol.Required("add_another", default=False): BooleanSelector(),
                }
            ),
            description_placeholders={
                "camera_count": str(len(self._cameras)),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return EcotrendIstaCzOptionsFlow(config_entry)


class EcotrendIstaCzOptionsFlow(OptionsFlow):
    """Handle options flow for ista EcoTrend CZ."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._cameras: list[dict[str, str]] = list(config_entry.data.get(CONF_CAMERAS, []))

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["credentials", "cameras", "add_camera"],
        )

    async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle credentials options."""
        if user_input is not None:
            new_data = dict(self.config_entry.data)
            new_data.update(user_input)
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="credentials",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=self.config_entry.data.get(CONF_USERNAME, ""),
                    ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                    vol.Required(
                        CONF_PASSWORD,
                        default=self.config_entry.data.get(CONF_PASSWORD, ""),
                    ): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
                    vol.Optional(
                        CONF_ADDON_HOST,
                        default=self.config_entry.data.get(CONF_ADDON_HOST, DEFAULT_ADDON_HOST),
                    ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                    vol.Optional(
                        CONF_ADDON_PORT,
                        default=self.config_entry.data.get(CONF_ADDON_PORT, DEFAULT_ADDON_PORT),
                    ): NumberSelector(NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX)),
                    vol.Optional(
                        CONF_PANEL_TITLE,
                        default=self.config_entry.data.get(CONF_PANEL_TITLE, DEFAULT_NAME),
                    ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                    vol.Optional(
                        CONF_PANEL_ICON,
                        default=self.config_entry.data.get(CONF_PANEL_ICON, DEFAULT_ICON),
                    ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                }
            ),
        )

    async def async_step_cameras(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show list of cameras to edit or remove."""
        if not self._cameras:
            return self.async_abort(reason="no_cameras")

        camera_options = []
        for i, cam in enumerate(self._cameras):
            tab_name = TABS.get(cam.get(CONF_TAB, ""), cam.get(CONF_TAB, ""))
            interval_name = INTERVALS.get(cam.get(CONF_INTERVAL, ""), cam.get(CONF_INTERVAL, ""))
            comparison_name = COMPARISONS.get(cam.get(CONF_COMPARISON, ""), cam.get(CONF_COMPARISON, ""))
            camera_options.append({
                "value": str(i),
                "label": f"{tab_name} - {interval_name} - {comparison_name}",
            })

        if user_input is not None:
            camera_index = int(user_input.get("camera_select", 0))
            # Remove the selected camera
            if 0 <= camera_index < len(self._cameras):
                self._cameras.pop(camera_index)
                new_data = dict(self.config_entry.data)
                new_data[CONF_CAMERAS] = self._cameras
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data=new_data,
                )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="cameras",
            data_schema=vol.Schema(
                {
                    vol.Required("camera_select"): SelectSelector(
                        SelectSelectorConfig(
                            options=camera_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            description_placeholders={
                "action": "remove",
            },
        )

    async def async_step_add_camera(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add a new camera."""
        errors: dict[str, str] = {}

        if user_input is not None:
            tab = user_input.get(CONF_TAB)
            comparison = user_input.get(CONF_COMPARISON)

            # Validate comparison is valid for tab
            if comparison not in VALID_COMPARISONS.get(tab, []):
                errors["base"] = "invalid_comparison"
            else:
                camera_config = {
                    CONF_TAB: user_input.get(CONF_TAB),
                    CONF_INTERVAL: user_input.get(CONF_INTERVAL),
                    CONF_COMPARISON: user_input.get(CONF_COMPARISON),
                    CONF_THEME: user_input.get(CONF_THEME, "auto"),
                    CONF_UPDATE_INTERVAL: user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                    CONF_UPDATE_TIME: user_input.get(CONF_UPDATE_TIME, DEFAULT_UPDATE_TIME),
                }
                self._cameras.append(camera_config)

                new_data = dict(self.config_entry.data)
                new_data[CONF_CAMERAS] = self._cameras
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data=new_data,
                )
                return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="add_camera",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TAB): SelectSelector(
                        SelectSelectorConfig(
                            options=[{"value": k, "label": v} for k, v in TABS.items()],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_INTERVAL): SelectSelector(
                        SelectSelectorConfig(
                            options=[{"value": k, "label": v} for k, v in INTERVALS.items()],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_COMPARISON): SelectSelector(
                        SelectSelectorConfig(
                            options=[{"value": k, "label": v} for k, v in COMPARISONS.items()],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(CONF_THEME, default="auto"): SelectSelector(
                        SelectSelectorConfig(
                            options=[{"value": k, "label": v} for k, v in THEMES.items()],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): NumberSelector(
                        NumberSelectorConfig(min=60, max=10080, step=60, mode=NumberSelectorMode.BOX, unit_of_measurement="min")
                    ),
                    vol.Optional(CONF_UPDATE_TIME, default=DEFAULT_UPDATE_TIME): TimeSelector(),
                }
            ),
            errors=errors,
        )
