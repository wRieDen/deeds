"""The Deeds Integration"""
import logging
from homeassistant.helpers import discovery
from .const import *

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Set up this component using YAML."""
    if config.get(DOMAIN) is None:
        return True

    platform_config = config[DOMAIN].get(CONF_SENSORS, {})

    # If platform is not enabled, skip.
    if not platform_config:
        return False

    for entry in platform_config:
        hass.async_create_task(discovery.async_load_platform(hass, PLATFORM, DOMAIN, entry, config))
        # hass.async_create_task(discovery.async_load_platform(hass, "button", DOMAIN, entry, config))

    return True


async def async_remove_entry(hass, config_entry):
    """Handle removal of an entry."""
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, PLATFORM)
        _LOGGER.info("Successfully removed sensor from the Deeds integration")
    except ValueError:
        pass


async def update_listener(hass, entry):
    """Update listener."""
    entry.data = entry.options
    await hass.config_entries.async_forward_entry_unload(entry, PLATFORM)
    hass.async_add_job(hass.config_entries.async_forward_entry_setup(entry, PLATFORM))
