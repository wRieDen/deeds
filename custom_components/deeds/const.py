""" Constants """
import voluptuous as vol

# from datetime import datetime, timedelta, timezone
import datetime
import dateutil.relativedelta
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_NAME, CONF_PATH
import re

from homeassistant.helpers.template import relative_time, strptime


class DeedsDate(dateutil.relativedelta.relativedelta):
    """date class"""

    def __init__(
        self,
        years=0,
        months=0,
        days=0,
        leapdays=0,
        weeks=0,
        hours=0,
        minutes=0,
        seconds=0,
        microseconds=0,
        year=None,
        month=None,
        day=None,
        weekday=None,
        yearday=None,
        nlyearday=None,
        hour=None,
        minute=None,
        second=None,
        microsecond=None,
        week=0,
        monday=0,
        tuesday=0,
        wednesday=0,
        thursday=0,
        friday=0,
        saturday=0,
        sunday=0,
        timezone=None,
    ):
        super().__init__(
            years=years,
            months=months,
            days=days,
            leapdays=leapdays,
            weeks=weeks,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            microseconds=microseconds,
            year=year,
            month=month,
            day=day,
            weekday=weekday,
            yearday=yearday,
            nlyearday=nlyearday,
            hour=hour,
            minute=minute,
            second=second,
            microsecond=microsecond,
        )

        self.has_absolute_values = any(x is not None for x in (self.year, self.month, self.day, self.hour, self.minute, self.second, self.microsecond))
        self.has_relative_values = any(x not in (None, 0) for x in (self.years, self.months, self.weeks, self.days, self.hours, self.minutes, self.seconds, self.microseconds))
        self.is_absolute = self.has_absolute_values and not self.has_relative_values
        self.is_relative = self.has_relative_values and not self.has_absolute_values

        self.monday = monday
        self.tuesday = tuesday
        self.wednesday = wednesday
        self.thursday = thursday
        self.friday = friday
        self.saturday = saturday
        self.sunday = sunday
        self.timezone = timezone
        self.weekdays = {
            "monday": monday,
            "tuesday": tuesday,
            "wednesday": wednesday,
            "thursday": thursday,
            "friday": friday,
            "saturday": saturday,
            "sunday": sunday,
        }

        if self.timezone is None:
            self.timezone = datetime.datetime.now().astimezone().tzinfo

    @classmethod
    def from_string(cls, text):

        date = None

        if text == "now":
            date = datetime.datetime.now().astimezone()
        elif text == "today":
            date = datetime.datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)

        # standard formats, preferred: 2021-5-23 21:33:12
        try:
            date = dateutil.parser.isoparse(text)
        except:
            pass

        if date is not None:
            return cls(
                year=date.year,
                month=date.month,
                day=date.day,
                hour=date.hour,
                minute=date.minute,
                second=date.second,
                timezone=date.tzinfo,
            )

        # flexible format eg: "1m 2d 21h"
        match = re.match(
            r"^(?:"
            r"(?P<year>\d*\.?\d+)\s*(y|year|years|yearly)|"
            r"(?P<month>\d*\.?\d+)\s*(m|month|months|monthly)|"
            r"(?P<day>\d*\.?\d+)\s*(d|day|days|daily)|"
            r"(?P<hour>\d*\.?\d+)\s*(h|hour|hours|hourly)|"
            r"(?P<minute>\d*\.?\d+)\s*(min|minute|minutes)|"
            r"(?P<second>\d*\.?\d+)\s*(s|sec|second|seconds)|"
            r"(?P<week>\d*\.?\d+)\s*(w|week|weeks|weekly)|"
            r"(?P<monday>\d*)\s*(mo|mon|monday|mondays)|"
            r"(?P<tuesday>\d*)\s*(tu|tue|tues|tuesday|tuesdays)|"
            r"(?P<wednesday>\d*)\s*(we|wed|wednesday|wednesdays)|"
            r"(?P<thursday>\d*)\s*(th|thu|thur|thurs|thursday|thursdays)|"
            r"(?P<friday>\d*)\s*(fr|fri|friday|fridays)|"
            r"(?P<saturday>\d*)\s*(sa|sat|saturday|saturdays)|"
            r"(?P<sunday>\d*)\s*(su|sun|sunday|sundays)|"
            r"[\s\-_:.])*$",
            text,
        )

        if match is not None:
            groups = {k: (1 if v == "" else v) for k, v in match.groupdict().items() if v is not None}

            return cls(
                years=int(groups.get("year", 0)),
                months=int(groups.get("month", 0)),
                days=int(groups.get("day", 0)),
                hours=int(groups.get("hour", 0)),
                minutes=int(groups.get("minute", 0)),
                seconds=int(groups.get("second", 0)),
                weeks=int(groups.get("week", 0)),
                monday=int(groups.get("monday", 0)),
                tuesday=int(groups.get("tuesday", 0)),
                wednesday=int(groups.get("wednesday", 0)),
                thursday=int(groups.get("thursday", 0)),
                friday=int(groups.get("friday", 0)),
                saturday=int(groups.get("saturday", 0)),
                sunday=int(groups.get("sunday", 0)),
            )

        else:
            return None

    @classmethod
    def from_datetime(cls, date):
        return cls(
            year=date.year,
            month=date.month,
            day=date.day,
            hour=date.hour,
            minute=date.minute,
            second=date.second,
            timezone=date.tzinfo,
        )

    def has_weekday_attribute(self):
        return any({v > 0 for v in self.weekdays.values()})

    def get_timedelta(self):
        return datetime.timedelta(
            weeks=self.weeks,
            days=self.day,
            hours=self.hour,
            minutes=self.minute,
            seconds=self.second,
        )

    def get_datetime(self):
        return datetime.datetime(
            year=self.year,
            month=self.month,
            day=self.day,
            hour=self.hour,
            minute=self.minute,
            second=self.second,
            tzinfo=self.timezone,
        )

    def is_valid_date(self):
        try:
            if self.is_absolute and self.get_datetime() is not None:
                return True
            return False

        except ValueError as e:
            print(f"value error: {e}")
            print(f"invalid date: {self.print()}")
            return False

    def is_valid_period(self):
        if self.is_relative:
            return True
        return False

    def get_max_relative_unit(self):
        for k, v in {
            "years": self.years,
            "months": self.months,
            "weeks": self.weeks,
            "days": self.days,
            "hours": self.hours,
            "minutes": self.minutes,
            "seconds": self.seconds,
            "microseconds": self.microseconds,
        }.items():
            if v is not None and v > 0:
                return k
        return None

    def print(self):
        print(f"year: {self.year}, month: {self.month}, day: {self.day}, hour: {self.hour}, minute: {self.minute}, second: {self.second}, weekdays: {self.weekdays}")


def check_date(value):
    dd = DeedsDate.from_string(value)
    if dd is not None and dd.is_valid_date():
        return dd

    raise vol.Invalid(f"Invalid Date: {value}")


def check_period(value):
    dd = DeedsDate.from_string(value)
    if dd is not None and dd.is_valid_period():
        return dd

    raise vol.Invalid(f"Invalid Period: {value}")


def check_date_period(value):
    dd = DeedsDate.from_string(value)
    if dd is not None and (dd.is_valid_date() or dd.is_valid_period()):
        return dd

    raise vol.Invalid(f"Invalid Date or Period: {value}")


def check_bool_int(value):
    if isinstance(value, bool):
        if value:
            return -1
        return 0

    if isinstance(value, int) and value >= 0:
        return value

    raise vol.Invalid(f"Invalid Input: {value}")


def check_round_up(value):
    if value in (True, False, "years", "months", "weeks", "days", "hours", "minutes"):
        return value

    raise vol.Invalid(f"Invalid Input: {value}")


# Base component constants
DOMAIN = "deeds"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "1.0.0"
PLATFORM = "sensor"

# API call
API_SERVICE = "api_call"
API_NAME = "name"
API_ACTION = "action"
API_ARGS = "args"

API_SCHEMA = vol.Schema(
    {
        vol.Required(API_NAME): cv.string,
        vol.Required(API_ACTION): cv.string,
        vol.Optional(API_ARGS): dict,
    }
)

# Attributes
ATTRIBUTION = "Sensor data calculated by Deeds Integration"
ATTR_LAST_COMPLETION = "last_completion"
ATTR_NEXT_COMPLETION = "next_completion"
ATTR_NEXT_INTERVAL = "next_interval"
ATTR_RATING = "rating"
ATTR_SUCCESSFUL_COMPLETIONS = "successful_completions"
ATTR_MISSED_COMPLETIONS = "missed_completions"
ATTR_CURRENT_STREAK = "current_streak"
ATTR_LONGEST_STREAK = "longest_streak"
ATTR_REMAINING_SECONDS = "remaining_seconds"
ATTR_REMAINING_TIME = "remaining_time"
ATTR_REMIND = "remind"
ATTR_VALID = "valid"

# Storage
STORAGE_KEY = "deeds"
STORAGE_VERSION = 1

STORE_LAST_COMPLETION = "last_completion"
STORE_NEXT_COMPLETION = "next_completion"
STORE_NEXT_INTERVAL = "next_interval"
STORE_RATING = "rating"
STORE_SUCCESSFUL_COMPLETIONS = "successful_completions"
STORE_MISSED_COMPLETIONS = "missed_completions"
STORE_CURRENT_STREAK = "current_streak"
STORE_LONGEST_STREAK = "longest_streak"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Configuration
CONF_SENSOR = "sensor"
CONF_ENABLED = "enabled"
CONF_DATE = "date"
CONF_DATE_TEMPLATE = "date_template"
CONF_SENSORS = "sensors"
CONF_UNIT_OF_MEASUREMENT = "unit_of_measurement"
CONF_ID_PREFIX = "id_prefix"

# general config
CONF_NAME = "name"
CONF_COMMENT = "comment"

# icon config
CONF_ICON_NORMAL = "icon_normal"
CONF_ICON_TODAY = "icon_today"
CONF_ICON_SOON = "icon_soon"

# time config
CONF_REPEAT = "repeat"  # number of times to repeat activity (True: unlimited or number)
CONF_START = "start"  # date on which the activity should be completed the first time
CONF_MAX_INTERVAL = "max_interval"  # maximum time between two subsequent activity completions
CONF_FIXED_INTERVAL = "fixed_interval"  # time between two activity completions
CONF_ROUND_UP = "round_up"  # rounding up the to the next month, day, hour etc...
CONF_REMINDER_PERIOD = "reminder_period"  # time window where reminders are activated for activity
CONF_VALID_PERIOD = "valid_period"  # time window where activity completion is accepted
CONF_COUNT = "count"  # time window where activity completion is accepted
CONF_RESCHEDULE_INTERVAL = "reschedule_interval"

# Defaults
DEFAULT_NAME = DOMAIN
DEFAULT_ICON_NORMAL = "mdi:calendar-blank"
DEFAULT_ICON_TODAY = "mdi:calendar-star"
DEFAULT_ICON_SOON = "mdi:calendar"
DEFAULT_UNIT_OF_MEASUREMENT = "Days"
DEFAULT_ID_PREFIX = "deeds_"
DEFAULT_COUNT = 1
DEFAULT_ROUND_UP = True
DEFAULT_REPEAT = True
DEFAULT_START = "now"
DEFAULT_MAX_INTERVAL = "1d"
DEFAULT_FIXED_INTERVAL = "1d"
DEFAULT_REMINDER_PERIOD = "1d"
DEFAULT_VALID_PERIOD = "1y"


# INTERVAL_SCHEMA = vol.Schema(
#     {vol.Required(vol.Any(CONF_MAX_INTERVAL, CONF_FIXED_INTERVAL, msg=CONF_DATE_REQD_ERROR)): object},
#     extra=vol.ALLOW_EXTRA,
# )

# SENSOR_CONFIG_SCHEMA = vol.Schema(
#     {
#         vol.Required(CONF_NAME): cv.string,
#         vol.Optional(CONF_COMMENT): cv.string,
#         vol.Optional(CONF_ICON_NORMAL, default=DEFAULT_ICON_NORMAL): cv.icon,
#         vol.Optional(CONF_ICON_TODAY, default=DEFAULT_ICON_TODAY): cv.icon,
#         vol.Optional(CONF_ICON_SOON, default=DEFAULT_ICON_SOON): cv.icon,
#         vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=DEFAULT_UNIT_OF_MEASUREMENT): cv.string,
#         vol.Optional(CONF_ID_PREFIX, default=DEFAULT_ID_PREFIX): cv.string,
#         vol.Optional(CONF_REPEAT, default=DEFAULT_REPEAT): check_bool_int,
#         vol.Optional(CONF_START, default=DEFAULT_START): check_date_period,
#         vol.Optional(CONF_ROUND_UP, default=DEFAULT_ROUND_UP): check_round_up,
#         vol.Exclusive(CONF_MAX_INTERVAL, "interval"): check_period,
#         vol.Exclusive(CONF_FIXED_INTERVAL, "interval"): check_period,
#         vol.Optional(CONF_REMINDER_PERIOD, default=DEFAULT_REMINDER_PERIOD): check_period,
#         vol.Optional(CONF_VALID_PERIOD, default=DEFAULT_VALID_PERIOD): check_period,
#         vol.Optional(CONF_COUNT, default=DEFAULT_COUNT): int,
#     }
# )


# SENSOR_SCHEMA = vol.All(SENSOR_CONFIG_SCHEMA, INTERVAL_SCHEMA)

# CONFIG_SCHEMA = vol.Schema(
#     {DOMAIN: vol.Schema({vol.Optional(CONF_SENSORS): vol.All(cv.ensure_list, [SENSOR_SCHEMA])})},
#     extra=vol.ALLOW_EXTRA,
# )


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_SENSORS): vol.All(
                    cv.ensure_list,
                    [
                        vol.All(
                            vol.Schema(
                                {
                                    vol.Required(CONF_NAME): cv.string,
                                    vol.Optional(CONF_COMMENT): cv.string,
                                    vol.Optional(CONF_ICON_NORMAL, default=DEFAULT_ICON_NORMAL): cv.icon,
                                    vol.Optional(CONF_ICON_TODAY, default=DEFAULT_ICON_TODAY): cv.icon,
                                    vol.Optional(CONF_ICON_SOON, default=DEFAULT_ICON_SOON): cv.icon,
                                    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=DEFAULT_UNIT_OF_MEASUREMENT): cv.string,
                                    vol.Optional(CONF_ID_PREFIX, default=DEFAULT_ID_PREFIX): cv.string,
                                    vol.Optional(CONF_REPEAT, default=DEFAULT_REPEAT): check_bool_int,
                                    vol.Optional(CONF_START): check_date_period,
                                    vol.Optional(CONF_ROUND_UP, default=DEFAULT_ROUND_UP): check_round_up,
                                    vol.Exclusive(CONF_MAX_INTERVAL, "interval"): check_period,
                                    vol.Exclusive(CONF_FIXED_INTERVAL, "interval"): check_period,
                                    vol.Optional(CONF_REMINDER_PERIOD, default=DEFAULT_REMINDER_PERIOD): check_period,
                                    vol.Optional(CONF_VALID_PERIOD, default=DEFAULT_VALID_PERIOD): check_period,
                                    vol.Optional(CONF_COUNT, default=DEFAULT_COUNT): int,
                                    vol.Optional(CONF_RESCHEDULE_INTERVAL): check_period,
                                }
                            ),
                            vol.Schema(
                                {
                                    vol.Required(vol.Any(CONF_MAX_INTERVAL, CONF_FIXED_INTERVAL)): object,
                                },
                                extra=vol.ALLOW_EXTRA,
                            ),
                        )
                    ],
                )
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


ICON = DEFAULT_ICON_NORMAL
