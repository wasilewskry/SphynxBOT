import datetime as dt

import aiohttp


def trim_by_paragraph(text: str, fallback_length: int = 900) -> str:
    """Trims text to under maximum set length. Tries not to break up paragraphs if possible."""
    paragraphs = text.split('\n')
    trimmed = paragraphs[0]
    for p in paragraphs[1:]:
        if len(trimmed) + len(p) < fallback_length:
            trimmed += '\n' + p
        else:
            break
    if len(trimmed) > fallback_length:
        trimmed = trimmed[:fallback_length - 3] + '...'
    return trimmed


def calculate_age(born: dt.date, died: dt.date = None) -> int:
    """Calculates someone's current age in years. Calculates age at death if second date is provided."""
    last_alive = died if died else dt.date.today()
    return last_alive.year - born.year - ((last_alive.month, last_alive.day) < (born.month, born.day))


async def get_as_json(url: str):
    """Returns a parsed json response from url."""
    async with aiohttp.ClientSession() as cs:
        async with cs.get(url) as r:
            return await r.json()
