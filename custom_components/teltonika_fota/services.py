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
    ATTR_IMEI,
    DOMAIN,
    SERVICE_BULK_CANCEL_TASKS,
    SERVICE_CANCEL_TASK,
    SERVICE_CREATE_CONFIG_TASK,
    SERVICE_CREATE_FIRMWARE_TASK,
    SERVICE_REFRESH_DEVICES,
    SERVICE_RETRY_FAILED_TASKS,
)

_LOGGER = logging.getLogger(__name__)

# Service schemas
SERVICE_REFRESH_DEVICES_SCHEMA = vol.Schema({})

SERVICE_CREATE_FIRMWARE_TASK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_IMEI): cv.string,
        vol.Required("firmware_id"): cv.positive_int,
    }
)

SERVICE_CREATE_CONFIG_TASK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_IMEI): cv.string,
        vol.Required("config_id"): cv.positive_int,
    }
)

SERVICE_CANCEL_TASK_SCHEMA = vol.Schema(
    {
        vol.Required("task_id"): cv.positive_int,
    }
)

SERVICE_BULK_CANCEL_TASKS_SCHEMA = vol.Schema(
    {
        vol.Required("task_ids"): vol.All(cv.ensure_list, [cv.positive_int]),
    }
)

SERVICE_RETRY_FAILED_TASKS_SCHEMA = vol.Schema(
    {
        vol.Required("batch_id"): cv.positive_int,
    }
)


def _get_first_api(hass: HomeAssistant) -> TeltonikaFotaApi | None:
    """Get the first available API client."""
    for entry_data in hass.data.get(DOMAIN, {}).values():
        if isinstance(entry_data, dict) and "api" in entry_data:
            return entry_data["api"]
    return None


def _get_api_for_device(hass: HomeAssistant, imei: str) -> TeltonikaFotaApi | None:
    """Get the API client that manages a specific device."""
    for entry_data in hass.data.get(DOMAIN, {}).values():
        if isinstance(entry_data, dict):
            coordinator = entry_data.get("coordinator")
            if coordinator and imei in coordinator.data.devices:
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

    async def async_create_firmware_task(call: ServiceCall) -> dict[str, Any]:
        """Handle create_firmware_task service call."""
        imei = call.data[ATTR_IMEI]
        firmware_id = call.data["firmware_id"]

        api = _get_api_for_device(hass, imei)
        if not api:
            api = _get_first_api(hass)

        if not api:
            raise HomeAssistantError("No Teltonika FOTA integration configured")

        try:
            result = await api.async_create_firmware_task(imei, firmware_id)
            _LOGGER.info("Created firmware task for device %s", imei)
            return result
        except TeltonikaFotaApiError as err:
            raise HomeAssistantError(f"Failed to create firmware task: {err}") from err

    async def async_create_config_task(call: ServiceCall) -> dict[str, Any]:
        """Handle create_config_task service call."""
        imei = call.data[ATTR_IMEI]
        config_id = call.data["config_id"]

        api = _get_api_for_device(hass, imei)
        if not api:
            api = _get_first_api(hass)

        if not api:
            raise HomeAssistantError("No Teltonika FOTA integration configured")

        try:
            result = await api.async_create_config_task(imei, config_id)
            _LOGGER.info("Created config task for device %s", imei)
            return result
        except TeltonikaFotaApiError as err:
            raise HomeAssistantError(
                f"Failed to create configuration task: {err}"
            ) from err

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

    async def async_bulk_cancel_tasks(call: ServiceCall) -> dict[str, Any]:
        """Handle bulk_cancel_tasks service call."""
        task_ids = call.data["task_ids"]

        api = _get_first_api(hass)
        if not api:
            raise HomeAssistantError("No Teltonika FOTA integration configured")

        try:
            result = await api.async_bulk_cancel_tasks(task_ids)
            _LOGGER.info("Bulk cancelled tasks: %s", task_ids)
            return result
        except TeltonikaFotaApiError as err:
            raise HomeAssistantError(f"Failed to bulk cancel tasks: {err}") from err

    async def async_retry_failed_tasks(call: ServiceCall) -> dict[str, Any]:
        """Handle retry_failed_tasks service call."""
        batch_id = call.data["batch_id"]

        api = _get_first_api(hass)
        if not api:
            raise HomeAssistantError("No Teltonika FOTA integration configured")

        try:
            result = await api.async_retry_failed_tasks(batch_id)
            _LOGGER.info("Retried failed tasks in batch %s", batch_id)
            return result
        except TeltonikaFotaApiError as err:
            raise HomeAssistantError(f"Failed to retry tasks: {err}") from err

    # Register all services
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_DEVICES,
        async_refresh_devices,
        schema=SERVICE_REFRESH_DEVICES_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_FIRMWARE_TASK,
        async_create_firmware_task,
        schema=SERVICE_CREATE_FIRMWARE_TASK_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_CONFIG_TASK,
        async_create_config_task,
        schema=SERVICE_CREATE_CONFIG_TASK_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CANCEL_TASK,
        async_cancel_task,
        schema=SERVICE_CANCEL_TASK_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_BULK_CANCEL_TASKS,
        async_bulk_cancel_tasks,
        schema=SERVICE_BULK_CANCEL_TASKS_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RETRY_FAILED_TASKS,
        async_retry_failed_tasks,
        schema=SERVICE_RETRY_FAILED_TASKS_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    _LOGGER.debug("Teltonika FOTA services registered")


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload Teltonika FOTA services."""
    hass.services.async_remove(DOMAIN, SERVICE_REFRESH_DEVICES)
    hass.services.async_remove(DOMAIN, SERVICE_CREATE_FIRMWARE_TASK)
    hass.services.async_remove(DOMAIN, SERVICE_CREATE_CONFIG_TASK)
    hass.services.async_remove(DOMAIN, SERVICE_CANCEL_TASK)
    hass.services.async_remove(DOMAIN, SERVICE_BULK_CANCEL_TASKS)
    hass.services.async_remove(DOMAIN, SERVICE_RETRY_FAILED_TASKS)

    _LOGGER.debug("Teltonika FOTA services unloaded")
