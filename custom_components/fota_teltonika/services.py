"""Services for Teltonika FOTA integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.exceptions import HomeAssistantError

from .api import TeltonikaFotaApi, TeltonikaFotaApiError
from .const import (
    DOMAIN,
    SERVICE_CANCEL_TASK,
    SERVICE_REFRESH_DEVICES,
)

_LOGGER = logging.getLogger(__name__)

# Service schemas
SERVICE_REFRESH_DEVICES_SCHEMA = vol.Schema({})

SERVICE_CANCEL_TASK_SCHEMA = vol.Schema(
    {
        vol.Required("task_id"): cv.positive_int,
    }
)


def _get_first_api(hass: HomeAssistant) -> TeltonikaFotaApi | None:
    """Get the first available API client."""
    for entry_data in hass.data.get(DOMAIN, {}).values():
        if isinstance(entry_data, dict) and "api" in entry_data:
            return entry_data["api"]
    return None


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Teltonika FOTA integration."""

    async def async_refresh_devices(call: ServiceCall) -> None:
        """Handle refresh_devices service call."""
        for entry_data in hass.data.get(DOMAIN, {}).values():
            if isinstance(entry_data, dict):
                coordinator = entry_data.get("coordinator")
                if coordinator:
                    await coordinator.async_request_refresh()
        _LOGGER.info("Teltonika FOTA devices refreshed")

    async def async_cancel_task(call: ServiceCall) -> dict[str, Any]:
        """Handle cancel_task service call."""
        task_id = call.data["task_id"]

        api = _get_first_api(hass)
        if not api:
            raise HomeAssistantError("No Teltonika FOTA integration configured")

        try:
            result = await api.async_cancel_task(task_id)
            _LOGGER.info("Cancelled task %s", task_id)
            return result
        except TeltonikaFotaApiError as err:
            raise HomeAssistantError(f"Failed to cancel task: {err}") from err

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_DEVICES,
        async_refresh_devices,
        schema=SERVICE_REFRESH_DEVICES_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CANCEL_TASK,
        async_cancel_task,
        schema=SERVICE_CANCEL_TASK_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    _LOGGER.debug("Teltonika FOTA services registered")


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload Teltonika FOTA services."""
    hass.services.async_remove(DOMAIN, SERVICE_REFRESH_DEVICES)
    hass.services.async_remove(DOMAIN, SERVICE_CANCEL_TASK)

    _LOGGER.debug("Teltonika FOTA services unloaded")
