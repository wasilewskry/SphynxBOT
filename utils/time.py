import datetime as dt
import zoneinfo
from functools import lru_cache


@lru_cache(maxsize=None)
def get_timezones():
    return zoneinfo.available_timezones()


def next_datetime(current: dt.datetime, hour: int, minute: int) -> dt.datetime:
    repl = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
    while repl <= current:
        repl = repl + dt.timedelta(days=1)
    return repl
