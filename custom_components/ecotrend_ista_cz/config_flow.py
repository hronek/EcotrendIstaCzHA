"""Config flow for ista EcoTrend CZ integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import callback

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


class EcotrendIstaCzConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ista EcoTrend CZ."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input.get(CONF_PANEL_TITLE, DEFAULT_NAME),
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL, default=DEFAULT_URL): str,
                    vol.Required(CONF_PANEL_TITLE, default=DEFAULT_NAME): str,
                    vol.Required(CONF_PANEL_ICON, default=DEFAULT_ICON): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return EcotrendIstaCzOptionsFlow(config_entry)


class EcotrendIstaCzOptionsFlow:
    """Handle options flow for ista EcoTrend CZ."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_URL,
                        default=self.config_entry.data.get(CONF_URL, DEFAULT_URL),
                    ): str,
                    vol.Required(
                        CONF_PANEL_TITLE,
                        default=self.config_entry.data.get(CONF_PANEL_TITLE, DEFAULT_NAME),
                    ): str,
                    vol.Required(
                        CONF_PANEL_ICON,
                        default=self.config_entry.data.get(CONF_PANEL_ICON, DEFAULT_ICON),
                    ): str,
                }
            ),
        )
