from enum import Enum, IntEnum


class ReminderChannel(Enum):
    here = 1
    dm = 2


class ReminderType(IntEnum):
    single = 1
    daily = 2
