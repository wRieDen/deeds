""" Button """
from dateutil.relativedelta import relativedelta
from datetime import datetime, date

from homeassistant.helpers.entity import Entity, generate_entity_id

# from homeassistant.components.sensor import ENTITY_ID_FORMAT
from homeassistant.components.button import ENTITY_ID_FORMAT, ButtonEntity
from homeassistant.helpers import template as templater
from asyncio import create_task
from homeassistant.const import (
    ATTR_NAME,
    CONF_NAME,
    ATTR_ATTRIBUTION,
)
from .const import *


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the sensor platform."""
    async_add_entities([deeds(hass, discovery_info)], True)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform."""
    async_add_devices([deeds(hass, config_entry.data)], True)


class deeds(ButtonEntity):
    def __init__(self, hass, config):
        """Initialize the sensor."""
        self.hass = hass
        self.config = config
        self._name = config.get(CONF_NAME)
        self._id_prefix = config.get(CONF_ID_PREFIX)
        self.entity_id = generate_entity_id(ENTITY_ID_FORMAT, self._id_prefix + self._name, [])

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return self.config.get("unique_id", None)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    # @property
    # def extra_state_attributes(self):
    #     """Return the state attributes."""
    #     res = {}
    #     res[ATTR_ATTRIBUTION] = ATTRIBUTION
    #     res["test attr"] = "Hello there!"
    #     return res

    # @property
    # def icon(self):
    #     return self._icon

    # @property
    # def unit_of_measurement(self):
    #     """Return the unit this state is expressed in."""
    #     if self._state in ["Invalid Date", "Invalid Template"]:
    #         return
    #     return self._unit_of_measurement

    # def press(self) -> None:
    #    """Handle the button press."""

    async def async_press(self) -> None:
        """Handle the button press."""
        create_task(self.hass.services.async_call(DOMAIN, API_SERVICE, {ATTR_NAME: self._name, API_ACTION: "trigger"}))
