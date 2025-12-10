"""DataUpdateCoordinator for Teltonika FOTA."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import (
    TeltonikaFotaApi,
    TeltonikaFotaApiError,
    TeltonikaFotaAuthError,
)
from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    STATUS_ONLINE,
    TASK_STATUS_PENDING,
    TASK_STATUS_FAILED,
)

_LOGGER = logging.getLogger(__name__)


class TeltonikaFotaData:
    """Class to hold all Teltonika FOTA data."""

    def __init__(self) -> None:
        """Initialize the data holder."""
        self.devices: dict[str, dict[str, Any]] = {}  # keyed by IMEI
        self.tasks: list[dict[str, Any]] = []
        self.company_stats: dict[str, Any] = {}

    @property
    def total_devices(self) -> int:
        """Return total device count."""
        return len(self.devices)

    @property
    def online_devices(self) -> int:
        """Return online device count."""
        return sum(
            1
            for d in self.devices.values()
            if d.get("activity_status") == STATUS_ONLINE
        )

    @property
    def offline_devices(self) -> int:
        """Return offline device count."""
        return self.total_devices - self.online_devices

    @property
    def pending_tasks(self) -> int:
        """Return pending task count."""
        return sum(
            1
            for t in self.tasks
            if t.get("status") == TASK_STATUS_PENDING
        )

    @property
    def failed_tasks(self) -> int:
        """Return failed task count."""
        return sum(
            1
            for t in self.tasks
            if t.get("status") == TASK_STATUS_FAILED
        )

    @property
    def group_count(self) -> int:
        """Return group count from company stats."""
        return self.company_stats.get("group_count", 0)

    @property
    def task_count(self) -> int:
        """Return total task count from company stats."""
        return self.company_stats.get("task_count", 0)


class TeltonikaFotaCoordinator(DataUpdateCoordinator[TeltonikaFotaData]):
    """Coordinator to manage fetching Teltonika FOTA data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        api: TeltonikaFotaApi,
        update_interval: timedelta = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.api = api
        self._data = TeltonikaFotaData()

    async def _async_update_data(self) -> TeltonikaFotaData:
        """Fetch data from API."""
        data = TeltonikaFotaData()

        try:
            # Fetch devices
            _LOGGER.debug("Fetching devices from Teltonika FOTA API")
            devices = await self.api.async_get_all_devices()
            # Store devices with IMEI as string key
            data.devices = {str(d["imei"]): d for d in devices if "imei" in d}
            _LOGGER.debug("Fetched %d devices", len(data.devices))

            # Log first device structure for debugging (debug level)
            if devices and _LOGGER.isEnabledFor(logging.DEBUG):
                first_device = devices[0] if devices else {}
                _LOGGER.debug(
                    "Sample device fields: %s",
                    list(first_device.keys())
                )

            # Fetch tasks (recent/active)
            _LOGGER.debug("Fetching tasks from Teltonika FOTA API")
            tasks_result = await self.api.async_get_tasks()
            data.tasks = tasks_result.get("data", [])
            _LOGGER.debug("Fetched %d tasks", len(data.tasks))

            # Fetch company stats
            _LOGGER.debug("Fetching company stats from Teltonika FOTA API")
            data.company_stats = await self.api.async_get_company_stats()

        except TeltonikaFotaAuthError as err:
            _LOGGER.error("Authentication failed: %s", err)
            raise ConfigEntryAuthFailed(
                "Authentication failed. Please reconfigure the integration."
            ) from err
        except TeltonikaFotaApiError as err:
            _LOGGER.error("Error communicating with API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        self._data = data
        return data

    async def async_refresh_devices(self) -> None:
        """Force refresh device data."""
        await self.async_request_refresh()
