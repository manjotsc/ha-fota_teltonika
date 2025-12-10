"""Button platform for Teltonika FOTA."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import TeltonikaFotaApi
from .const import DOMAIN
from .coordinator import TeltonikaFotaCoordinator
from .sensor import _get_firmware_version, _get_device_name

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Teltonika FOTA buttons."""
    coordinator: TeltonikaFotaCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    api: TeltonikaFotaApi = hass.data[DOMAIN][entry.entry_id]["api"]

    entities: list[ButtonEntity] = []

    # Add cancel tasks button for each device
    for imei, device_data in coordinator.data.devices.items():
        entities.append(
            TeltonikaFotaCancelTasksButton(
                coordinator,
                api,
                entry,
                imei,
                device_data,
            )
        )

    # Add refresh button for account
    entities.append(
        TeltonikaFotaRefreshButton(
            coordinator,
            entry,
        )
    )

    async_add_entities(entities)


class TeltonikaFotaCancelTasksButton(
    CoordinatorEntity[TeltonikaFotaCoordinator],
    ButtonEntity,
):
    """Button to cancel all pending tasks for a device."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:cancel"

    def __init__(
        self,
        coordinator: TeltonikaFotaCoordinator,
        api: TeltonikaFotaApi,
        entry: ConfigEntry,
        imei: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._api = api
        self._imei = imei
        self._entry = entry

        self._attr_unique_id = f"{DOMAIN}_{imei}_cancel_tasks"
        self._attr_name = "Cancel Pending Tasks"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.data.devices.get(self._imei, {})
        model = device.get("model", "Unknown Device")
        firmware = _get_firmware_version(device)
        device_name = _get_device_name(device, self._imei)

        return DeviceInfo(
            identifiers={(DOMAIN, self._imei)},
            name=device_name,
            manufacturer="Teltonika",
            model=model,
            sw_version=firmware,
            configuration_url="https://fota.teltonika.lt",
        )

    @property
    def available(self) -> bool:
        """Return if button is available (has pending tasks)."""
        device = self.coordinator.data.devices.get(self._imei, {})
        task_queue = device.get("task_queue")
        # Available if there are tasks to cancel
        if task_queue and task_queue != "Empty":
            return True
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        device = self.coordinator.data.devices.get(self._imei, {})
        task_queue = device.get("task_queue")
        attrs = {"imei": self._imei}

        if task_queue and task_queue != "Empty" and isinstance(task_queue, list):
            attrs["pending_task_ids"] = [t.get("id") for t in task_queue if t.get("id")]
            attrs["task_count"] = len(task_queue)

        return attrs

    async def async_press(self) -> None:
        """Handle button press - cancel all pending tasks for this device."""
        device = self.coordinator.data.devices.get(self._imei, {})
        task_queue = device.get("task_queue")

        if not task_queue or task_queue == "Empty":
            _LOGGER.info("No pending tasks to cancel for device %s", self._imei)
            return

        if isinstance(task_queue, list):
            task_ids = [t.get("id") for t in task_queue if t.get("id")]
            if task_ids:
                try:
                    await self._api.async_bulk_cancel_tasks(task_ids)
                    _LOGGER.info(
                        "Cancelled %d tasks for device %s: %s",
                        len(task_ids),
                        self._imei,
                        task_ids,
                    )
                    # Refresh data after cancelling
                    await self.coordinator.async_request_refresh()
                except Exception as err:
                    _LOGGER.error("Failed to cancel tasks: %s", err)
                    raise


class TeltonikaFotaRefreshButton(
    CoordinatorEntity[TeltonikaFotaCoordinator],
    ButtonEntity,
):
    """Button to refresh all device data."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:refresh"

    def __init__(
        self,
        coordinator: TeltonikaFotaCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._entry = entry

        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_refresh"
        self._attr_name = "Refresh Data"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for the account 'device'."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"account_{self._entry.entry_id}")},
            name="Teltonika FOTA Account",
            manufacturer="Teltonika",
            model="FOTA Account",
            configuration_url="https://fota.teltonika.lt",
        )

    async def async_press(self) -> None:
        """Handle button press - refresh all data."""
        _LOGGER.info("Refreshing Teltonika FOTA data")
        await self.coordinator.async_request_refresh()
