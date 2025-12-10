"""Config flow for Teltonika FOTA integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import (
    TeltonikaFotaApi,
    TeltonikaFotaApiError,
    TeltonikaFotaAuthError,
)
from .const import (
    CONF_API_TOKEN,
    CONF_ENABLED_SENSORS,
    CONF_MONITORED_DEVICES,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL_MINUTES,
    MAX_SCAN_INTERVAL_MINUTES,
    SENSOR_KEYS,
    STATUS_ONLINE,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_TOKEN): str,
    }
)


class TeltonikaFotaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Teltonika FOTA."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._api_token: str | None = None
        self._account_info: dict[str, Any] = {}
        self._devices: list[dict[str, Any]] = []

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle the initial step - API token entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_token = user_input[CONF_API_TOKEN]

            # Validate the token
            session = async_get_clientsession(self.hass)
            api = TeltonikaFotaApi(session, api_token)

            try:
                # Validate token by fetching company stats
                self._account_info = await api.async_get_company_stats()

                # Fetch devices for selection
                self._devices = await api.async_get_all_devices()
                self._api_token = api_token

                # Move to account info confirmation step
                return await self.async_step_account()

            except TeltonikaFotaAuthError:
                errors["base"] = "invalid_auth"
            except TeltonikaFotaApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during configuration")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_account(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Show account info and confirm setup."""
        if user_input is not None:
            # Create unique ID from company info or token hash
            unique_id = str(self._account_info.get("company_id", ""))
            if not unique_id:
                # Fallback to token hash if no company_id
                unique_id = str(hash(self._api_token))[:16]

            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Teltonika FOTA ({len(self._devices)} devices)",
                data={CONF_API_TOKEN: self._api_token},
                options={
                    CONF_SCAN_INTERVAL: int(DEFAULT_SCAN_INTERVAL.total_seconds() / 60),
                    CONF_MONITORED_DEVICES: [
                        d["imei"] for d in self._devices if "imei" in d
                    ],
                },
            )

        # Build description with account info
        device_count = len(self._devices)
        online_count = sum(
            1
            for d in self._devices
            if d.get("activity_status") == STATUS_ONLINE
        )

        return self.async_show_form(
            step_id="account",
            description_placeholders={
                "device_count": str(device_count),
                "online_count": str(online_count),
            },
        )

    async def async_step_reauth(
        self,
        entry_data: dict[str, Any],
    ) -> FlowResult:
        """Handle reauthentication."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Confirm reauthentication."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_token = user_input[CONF_API_TOKEN]
            session = async_get_clientsession(self.hass)
            api = TeltonikaFotaApi(session, api_token)

            try:
                await api.async_validate_token()

                # Update the config entry with new token
                entry = self.hass.config_entries.async_get_entry(
                    self.context["entry_id"]
                )
                if entry:
                    self.hass.config_entries.async_update_entry(
                        entry,
                        data={CONF_API_TOKEN: api_token},
                    )
                    await self.hass.config_entries.async_reload(entry.entry_id)
                    return self.async_abort(reason="reauth_successful")

            except TeltonikaFotaAuthError:
                errors["base"] = "invalid_auth"
            except TeltonikaFotaApiError:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> TeltonikaFotaOptionsFlow:
        """Get the options flow for this handler."""
        return TeltonikaFotaOptionsFlow()


class TeltonikaFotaOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Teltonika FOTA."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current options
        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            int(DEFAULT_SCAN_INTERVAL.total_seconds() / 60),
        )

        # Get current enabled sensors
        current_sensors = self.config_entry.options.get(
            CONF_ENABLED_SENSORS,
            list(SENSOR_KEYS.keys()),  # Default to all sensors
        )

        # Build sensor options list
        sensor_options = [
            {"value": key, "label": label}
            for key, label in SENSOR_KEYS.items()
        ]

        # Build the options schema
        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=current_interval,
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL_MINUTES,
                        max=MAX_SCAN_INTERVAL_MINUTES,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="minutes",
                    )
                ),
                vol.Optional(
                    CONF_ENABLED_SENSORS,
                    default=current_sensors,
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=sensor_options,
                        multiple=True,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )
