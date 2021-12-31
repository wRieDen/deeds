""" Sensor """
import dateutil.parser
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, time, timedelta

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.components.sensor import ENTITY_ID_FORMAT, PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME, ATTR_ATTRIBUTION, ATTR_NAME, EVENT_STATE_CHANGED
from homeassistant.helpers.storage import Store
from homeassistant.helpers.json import JSONEncoder
from homeassistant.exceptions import HomeAssistantError

from .const import *


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the sensor platform."""
    async_add_entities([Deeds(hass, discovery_info)], True)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform."""
    async_add_devices([Deeds(hass, config_entry.data)], True)


class Deeds(SensorEntity):
    """Deeds Sensor Class"""

    instances = {}
    store = None
    stored_instances = {}

    def __init__(self, hass, config):
        self.hass = hass
        self.config = config

        self.init_done = False

        self._name = config.get(CONF_NAME)
        self.id_prefix = config.get(CONF_ID_PREFIX)
        self.entity_id = generate_entity_id(ENTITY_ID_FORMAT, self.id_prefix + self._name, [])

        self.icon_normal = config.get(CONF_ICON_NORMAL)
        self.icon_today = config.get(CONF_ICON_TODAY)
        self.icon_soon = config.get(CONF_ICON_SOON)

        self.repeat = config.get(CONF_REPEAT)
        self.start: DeedsDate = config.get(CONF_START)
        self.round_up = config.get(CONF_ROUND_UP)
        self.max_interval = config.get(CONF_MAX_INTERVAL)
        self.fixed_interval = config.get(CONF_FIXED_INTERVAL)
        self.reminder_period = config.get(CONF_REMINDER_PERIOD)
        self.valid_period = config.get(CONF_VALID_PERIOD)
        self.unit = config.get(CONF_UNIT_OF_MEASUREMENT, DEFAULT_UNIT_OF_MEASUREMENT)

        self.round_up_timedelta = relativedelta()
        if self.max_interval is not None:
            if self.round_up is True:
                self.round_up = self.max_interval.get_max_relative_unit()

            if self.start is not None:
                offset = self.start
            else:
                offset = DeedsDate(month=1, day=1, hour=0, minute=0, second=0)

            if self.round_up == "years":
                self.round_up_timedelta = relativedelta(years=1, month=offset.month, day=offset.day, hour=offset.hour, minute=offset.minute, second=offset.second, microsecond=0)
            elif self.round_up == "months":
                self.round_up_timedelta = relativedelta(months=1, day=offset.day, hour=offset.hour, minute=offset.minute, second=offset.second, microsecond=0)
            elif self.round_up == "days":
                self.round_up_timedelta = relativedelta(days=1, hour=offset.hour, minute=offset.minute, second=offset.second, microsecond=0)
            elif self.round_up == "hours":
                self.round_up_timedelta = relativedelta(hours=1, minute=offset.minute, second=offset.second, microsecond=0)
            elif self.round_up == "minutes":
                self.round_up_timedelta = relativedelta(minutes=1, second=offset.second, microsecond=0)

        if self.start is None and self.max_interval is not None:
            self.start = DeedsDate.from_datetime((datetime.datetime.now().astimezone().replace(microsecond=0) + self.max_interval) + self.round_up_timedelta)

        self.reschedule_interval = config.get(CONF_RESCHEDULE_INTERVAL)
        if self.reschedule_interval is None and self.max_interval is not None:
            self.reschedule_interval = DeedsDate(days=1)

        self.last_completion = None
        self.next_completion = None
        self.next_interval = None
        self.successful_completions = 0
        self.missed_completions = 0
        self.current_streak = 0
        self.longest_streak = 0
        self.reset()

        Deeds.instances[self.entity_id] = self

    async def async_added_to_hass(self):
        """Call when entity about to be added to hass."""
        await super().async_added_to_hass()

        if Deeds.store is None:
            Deeds.store = Store(self.hass, STORAGE_VERSION, STORAGE_KEY, encoder=JSONEncoder)
            try:
                store = await Deeds.store.async_load()
                if store is not None:
                    Deeds.stored_instances = store
            except HomeAssistantError as exc:
                print("Error loading last states", exc_info=exc)

            for k, v in Deeds.instances.items():
                if (attr := Deeds.stored_instances.get(k)) is not None:
                    v.attributes_from_dict(attr)
                    v.init_done = True

            await Deeds.init_api(self.hass)

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return self.config.get("unique_id", None)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    # @property
    # def state(self):
    #     """Return the name of the sensor."""
    #     return self.successful_completions

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        current_time = datetime.datetime.now().astimezone().replace(microsecond=0)
        remaining_time = self.next_completion - current_time

        if remaining_time.days < 0:
            remaining_time_str = "-" + str(current_time - self.next_completion)
        else:
            remaining_time_str = str(remaining_time)

        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_LAST_COMPLETION: None if self.last_completion is None else self.last_completion.isoformat(),
            ATTR_NEXT_COMPLETION: None if self.next_completion is None else self.next_completion.isoformat(),
            ATTR_NEXT_INTERVAL: None if self.next_interval is None else self.next_interval.isoformat(),
            ATTR_SUCCESSFUL_COMPLETIONS: self.successful_completions,
            ATTR_MISSED_COMPLETIONS: self.missed_completions,
            ATTR_CURRENT_STREAK: self.current_streak,
            ATTR_LONGEST_STREAK: self.longest_streak,
            ATTR_REMAINING_SECONDS: remaining_time / timedelta(seconds=1),
            ATTR_REMAINING_TIME: remaining_time_str,
            ATTR_REMIND: self.next_completion - self.reminder_period < current_time,
            ATTR_VALID: self.next_completion - self.valid_period < current_time,
        }

    @property
    def icon(self):
        return self.icon_normal

    @property
    def native_value(self):
        """Return the value reported by the sensor."""
        return self.successful_completions
        # return 0

    # @property
    # def native_unit_of_measurement(self):
    #     """Return the unit of measurement of the sensor, if any."""
    #     if hasattr(self, "_attr_native_unit_of_measurement"):
    #         return self._attr_native_unit_of_measurement
    #     if hasattr(self, "entity_description"):
    #         return self.entity_description.native_unit_of_measurement
    #     return None

    def reset(self):
        """Resets Attributes to their defaults"""
        self.last_completion = None
        self.next_completion = self.start.get_datetime().astimezone().replace(microsecond=0)
        self.next_interval = self.start.get_datetime().astimezone().replace(microsecond=0)
        self.successful_completions = 0
        self.missed_completions = 0
        self.current_streak = 0
        self.longest_streak = 0

    def attributes_to_dict(self):
        """Returns dict from attributes"""
        return {
            ATTR_LAST_COMPLETION: None if self.last_completion is None else self.last_completion.isoformat(),
            ATTR_NEXT_COMPLETION: None if self.next_completion is None else self.next_completion.isoformat(),
            ATTR_NEXT_INTERVAL: None if self.next_interval is None else self.next_interval.isoformat(),
            ATTR_SUCCESSFUL_COMPLETIONS: self.successful_completions,
            ATTR_MISSED_COMPLETIONS: self.missed_completions,
            ATTR_CURRENT_STREAK: self.current_streak,
            ATTR_LONGEST_STREAK: self.longest_streak,
        }

    def attributes_from_dict(self, attr):
        """Sets attributes from dict"""
        self.last_completion = Deeds.isostr_as_datetime(attr.get(ATTR_LAST_COMPLETION, self.last_completion))
        self.next_completion = Deeds.isostr_as_datetime(attr.get(ATTR_NEXT_COMPLETION, self.next_completion))
        self.next_interval = Deeds.isostr_as_datetime(attr.get(ATTR_NEXT_INTERVAL, self.next_interval))
        self.successful_completions = attr.get(ATTR_SUCCESSFUL_COMPLETIONS, self.successful_completions)
        self.missed_completions = attr.get(ATTR_MISSED_COMPLETIONS, self.missed_completions)
        self.current_streak = attr.get(ATTR_CURRENT_STREAK, self.current_streak)
        self.longest_streak = attr.get(ATTR_LONGEST_STREAK, self.longest_streak)

    @staticmethod
    async def store_state():
        """stores all states"""
        try:
            store = Deeds.stored_instances | {k: v.attributes_to_dict() for k, v in Deeds.instances.items()}
            await Deeds.store.async_save(store)
        except HomeAssistantError as exc:
            print("Error saving current states", exc_info=exc)

    async def async_update(self):
        """update the sensor"""
        if not self.init_done:
            return

        # self.next_completion = self.last_completion
        if self.is_overdue():
            self.current_streak = 0
            self.missed_completions += 1

            if self.reschedule_interval is not None:
                self.next_completion = (self.next_completion + self.reschedule_interval) + self.round_up_timedelta
            else:
                if self.max_interval is not None:
                    self.next_completion = (datetime.datetime.now().astimezone().replace(microsecond=0) + self.max_interval) + self.round_up_timedelta
                elif self.fixed_interval is not None:
                    self.next_completion = self.next_interval + self.fixed_interval
                self.next_interval = self.next_completion

            await Deeds.store_state()

    ### API Management ###
    @staticmethod
    async def init_api(hass: HomeAssistant):
        """Initialize API"""
        if not hass.services.has_service(DOMAIN, API_SERVICE):
            hass.services.async_register(DOMAIN, API_SERVICE, Deeds.handle_api_call, schema=API_SCHEMA)

    @staticmethod
    async def handle_api_call(call: ServiceCall):
        """Handles incoming API calls"""
        name = call.data.get(API_NAME)
        action = call.data.get(API_ACTION)

        for inst in [v for k, v in Deeds.instances.items() if (name in ["all", k])]:
            if action == "trigger":
                await inst.handle_trigger()
            elif action == "pause":
                pass
            elif action == "reset":
                await inst.handle_reset()
            else:
                pass

    def is_valid(self):
        return self.next_completion - self.valid_period < datetime.datetime.now().astimezone().replace(microsecond=0)

    def is_overdue(self):
        return self.next_completion < datetime.datetime.now().astimezone().replace(microsecond=0)

    async def handle_trigger(self):
        """Handles Trigger Events"""
        old_state = self.state

        if self.is_valid():
            self.last_completion = datetime.datetime.now().astimezone().replace(microsecond=0)
            if self.max_interval is not None:
                self.next_completion = (self.last_completion + self.max_interval) + self.round_up_timedelta
                self.next_interval = self.next_completion
            elif self.fixed_interval is not None:
                while self.next_interval < self.last_completion:
                    self.next_completion = self.next_interval + self.fixed_interval
                    self.next_interval = self.next_completion

            self.successful_completions += 1
            self.current_streak += 1

            await self.async_update_ha_state(force_refresh=True)
            await Deeds.store_state()

    async def handle_reset(self):
        """Handles Reset Events"""
        # await RestoreEntity.async_internal_will_remove_from_hass(self)
        self.reset()
        await self.async_update_ha_state(force_refresh=True)
        await Deeds.store_state()

    ### Helper Functions ###
    @staticmethod
    def isostr_as_datetime(timestr):
        """Returns a datetime object from an iso time string"""
        if timestr is None:
            return None

        if isinstance(timestr, datetime.datetime):
            return timestr

        try:
            return dateutil.parser.isoparse(timestr)
        except (dateutil.parser.ParserError, OverflowError):
            return None
