from enum import Enum, auto


class ReminderChannel(Enum):
    Here = auto()
    DM = auto()


class ReminderType(Enum):
    Single = auto()
    Daily = auto()
