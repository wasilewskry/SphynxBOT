import collections
import datetime as dt
from enum import Enum, auto

from discord import app_commands

from .models import Production


class CinemaEntity(Enum):
    person = auto()
    movie = auto()
    tv = auto()


def deduplicate_autocomplete_labels(choices: list[app_commands.Choice]) -> list[app_commands.Choice]:
    dupes = collections.defaultdict(int)
    for c in choices:
        name = c.name
        dupes[name] += 1
        if dupes[name] > 1:
            c.name += f" ({dupes[name]})"
    for c in choices:
        if dupes.get(c.name, 0) > 1:
            c.name += ' (1)'
    return choices


def prepare_production_autocomplete_choices(candidates: list[Production]) -> list[app_commands.Choice]:
    candidates = sorted(candidates, key=lambda x: x.popularity, reverse=True)
    for c in candidates:
        if c.release_date:
            c.title = f'{c.title} ({c.release_date.year})'
    choices = [app_commands.Choice(name=f'{c.title}', value=c.id) for c in candidates]
    return deduplicate_autocomplete_labels(choices)


def verbose_date(date: dt.datetime.date) -> str:
    return date.strftime('%d %B, %Y')
