"""Teltonika FOTA integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TeltonikaFotaApi
from .const import (
    CONF_API_TOKEN,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import TeltonikaFotaCoordinator
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

type TeltonikaFotaConfigEntry = ConfigEntry[TeltonikaFotaCoordinator]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Teltonika FOTA from configuration.yaml."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: TeltonikaFotaConfigEntry) -> bool:
    """Set up Teltonika FOTA from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Get API token from config
    api_token = entry.data[CONF_API_TOKEN]

    # Get scan interval from options or use default
    scan_interval_minutes = entry.options.get(
        CONF_SCAN_INTERVAL,
        DEFAULT_SCAN_INTERVAL.total_seconds() / 60,
    )
    scan_interval = timedelta(minutes=scan_interval_minutes)

    # Create API client with shared session
    session = async_get_clientsession(hass)
    api = TeltonikaFotaApi(session, api_token)

    # Create coordinator
    coordinator = TeltonikaFotaCoordinator(
        hass,
        api,
        update_interval=scan_interval,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator and api
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up services (only once for first entry)
    if len(hass.data[DOMAIN]) == 1:
        await async_setup_services(hass)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    _LOGGER.info(
        "Teltonika FOTA integration set up with %d devices",
        coordinator.data.total_devices,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: TeltonikaFotaConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    # Unload services if no entries left
    if not hass.data[DOMAIN]:
        await async_unload_services(hass)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: TeltonikaFotaConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
