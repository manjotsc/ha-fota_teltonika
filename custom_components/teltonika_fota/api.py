"""Teltonika FOTA API client."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from aiohttp import ClientResponseError, ClientTimeout

from .const import (
    BASE_URL,
    ENDPOINT_BATCHES,
    ENDPOINT_COMPANY_STATS,
    ENDPOINT_DEVICES,
    ENDPOINT_TASKS,
    ENDPOINT_TASKS_BULK_CANCEL,
)

_LOGGER = logging.getLogger(__name__)


class TeltonikaFotaApiError(Exception):
    """Base exception for Teltonika FOTA API errors."""


class TeltonikaFotaAuthError(TeltonikaFotaApiError):
    """Authentication error (401/403)."""


class TeltonikaFotaConnectionError(TeltonikaFotaApiError):
    """Connection error."""


class TeltonikaFotaApi:
    """Async client for Teltonika FOTA API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_token: str,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._api_token = api_token
        self._base_url = BASE_URL
        self._timeout = ClientTimeout(total=30)

    @property
    def _headers(self) -> dict[str, str]:
        """Return authorization headers."""
        return {
            "Authorization": f"Bearer {self._api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an API request."""
        url = f"{self._base_url}{endpoint}"

        try:
            async with self._session.request(
                method,
                url,
                headers=self._headers,
                params=params,
                json=json_data,
                timeout=self._timeout,
            ) as response:
                if response.status == 401:
                    raise TeltonikaFotaAuthError("Invalid or expired API token")
                if response.status == 403:
                    raise TeltonikaFotaAuthError("Access forbidden")
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as err:
            if isinstance(err, ClientResponseError):
                _LOGGER.error("API error %s: %s", err.status, err.message)
            raise TeltonikaFotaConnectionError(f"Connection error: {err}") from err

    async def async_validate_token(self) -> dict[str, Any]:
        """Validate the API token by fetching company stats."""
        return await self._request("GET", ENDPOINT_COMPANY_STATS)

    async def async_get_devices(
        self,
        imeis: list[str] | None = None,
        page: int = 1,
        per_page: int = 100,
    ) -> dict[str, Any]:
        """Get devices from FOTA."""
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if imeis:
            params["imei"] = ",".join(imeis)
        return await self._request("GET", ENDPOINT_DEVICES, params=params)

    async def async_get_all_devices(self) -> list[dict[str, Any]]:
        """Get all devices with pagination."""
        all_devices: list[dict[str, Any]] = []
        page = 1

        while True:
            result = await self.async_get_devices(page=page)
            devices = result.get("data", [])
            all_devices.extend(devices)

            # Check pagination
            meta = result.get("meta", {})
            last_page = meta.get("last_page", 1)
            if page >= last_page:
                break
            page += 1

        return all_devices

    async def async_get_tasks(
        self,
        task_ids: list[int] | None = None,
        page: int = 1,
        per_page: int = 100,
    ) -> dict[str, Any]:
        """Get tasks from FOTA."""
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if task_ids:
            params["id"] = ",".join(str(tid) for tid in task_ids)
        return await self._request("GET", ENDPOINT_TASKS, params=params)

    async def async_get_all_tasks(self) -> list[dict[str, Any]]:
        """Get all tasks with pagination."""
        all_tasks: list[dict[str, Any]] = []
        page = 1

        while True:
            result = await self.async_get_tasks(page=page)
            tasks = result.get("data", [])
            all_tasks.extend(tasks)

            meta = result.get("meta", {})
            last_page = meta.get("last_page", 1)
            if page >= last_page:
                break
            page += 1

        return all_tasks

    async def async_create_firmware_task(
        self,
        imei: str,
        firmware_id: int,
    ) -> dict[str, Any]:
        """Create a firmware update task for a device."""
        json_data = {
            "imei": imei,
            "firmware_id": firmware_id,
            "type": "firmware",
        }
        return await self._request("POST", ENDPOINT_TASKS, json_data=json_data)

    async def async_create_config_task(
        self,
        imei: str,
        config_id: int,
    ) -> dict[str, Any]:
        """Create a configuration update task for a device."""
        json_data = {
            "imei": imei,
            "configuration_id": config_id,
            "type": "configuration",
        }
        return await self._request("POST", ENDPOINT_TASKS, json_data=json_data)

    async def async_cancel_task(self, task_id: int) -> dict[str, Any]:
        """Cancel a specific task."""
        return await self._request(
            "POST",
            ENDPOINT_TASKS_BULK_CANCEL,
            json_data={"id_list": [task_id]},
        )

    async def async_bulk_cancel_tasks(
        self,
        task_ids: list[int],
    ) -> dict[str, Any]:
        """Bulk cancel multiple tasks."""
        return await self._request(
            "POST",
            ENDPOINT_TASKS_BULK_CANCEL,
            json_data={"id_list": task_ids},
        )

    async def async_get_batch(self, batch_id: int) -> dict[str, Any]:
        """Get batch information."""
        return await self._request("GET", f"{ENDPOINT_BATCHES}/{batch_id}")

    async def async_retry_failed_tasks(self, batch_id: int) -> dict[str, Any]:
        """Retry failed tasks in a batch."""
        return await self._request(
            "POST",
            f"{ENDPOINT_BATCHES}/{batch_id}/retryFailedTasks",
        )

    async def async_get_company_stats(self) -> dict[str, Any]:
        """Get company statistics."""
        return await self._request("GET", ENDPOINT_COMPANY_STATS)
