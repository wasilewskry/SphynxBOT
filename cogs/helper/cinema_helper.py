import datetime as dt
import json
import logging
import urllib.request
from copy import deepcopy
from functools import cache
from typing import Dict, List, Any

import discord
from async_lru import alru_cache

from config import tmdb_api_key
from utils.constants import COLOR_EMBED_DARK
from utils.misc import trim_by_paragraph, calculate_age, get_as_json

_log = logging.getLogger(__name__)


@cache
def tmdb_get_config():
    """Retrieves strings necessary for building links to images. Results are cached after first request."""
    _log.info('Retrieving config from TMDB')
    with urllib.request.urlopen(f'{TMDB_API_BASE_URL}/configuration?api_key={tmdb_api_key}') as r:
        return json.loads(r.read().decode())['images']


@alru_cache(maxsize=4096)
async def tmdb_get(endpoint: str, **kwargs: str):
    """Creates a request to a given endpoint. Accepts query parameters as keyword arguments."""
    url = f'{TMDB_API_BASE_URL}{endpoint}?api_key={tmdb_api_key}'
    for k, v in kwargs.items():
        url += f'&{k}={v}'
    return await get_as_json(url)


def standardize_credits(combined_credits: Dict[str, List[Dict[str, Any]]]):
    """Ensures tv credit fields use the same names as movie fields and merges credits for the same movie/show."""
    standardized = deepcopy(combined_credits)
    for credit_type, credit_list in standardized.items():
        first_occurrences = {}
        indices_to_remove = []
        for idx, c in enumerate(credit_list):
            if c['media_type'] == 'tv':
                c['title'] = c.pop('name')
                c['release_date'] = c.pop('first_air_date')
            if credit_type == 'cast':
                key = (c['id'], 'Acting')
            else:
                key = (c['id'], c['department'])
            if first_occurrences.get(key):
                if key[1] == 'Acting':
                    credit_list[first_occurrences[key]]['character'] += f", {c['character']}"
                else:
                    credit_list[first_occurrences[key]]['job'] += f", {c['job']}"
                indices_to_remove.append(idx)
            else:
                first_occurrences[key] = idx
            standardized[credit_type] = [c for idx, c in enumerate(credit_list) if idx not in indices_to_remove]
    return standardized


TMDB_API_BASE_URL = 'https://api.themoviedb.org/3'
TMDB_WEB_BASE_URL = 'https://www.themoviedb.org'
TMDB_IMAGE_BASE_URL = tmdb_get_config()['secure_base_url']
TMDB_BACKDROP_SIZES = tmdb_get_config()['backdrop_sizes']
TMDB_LOGO_SIZES = tmdb_get_config()['logo_sizes']
TMDB_POSTER_SIZES = tmdb_get_config()['poster_sizes']
TMDB_PROFILE_SIZES = tmdb_get_config()['profile_sizes']
TMDB_STILL_SIZES = tmdb_get_config()['still_sizes']


class Person:
    def __init__(self, person_id: int):
        self.id = person_id
        self.imdb_id = None
        self.name = None
        self.biography = None
        self.short_bio = None
        self.birthday = None
        self.place_of_birth = None
        self.deathday = None
        self.age = None
        self.gender = None
        self.homepage = None
        self.known_for_department = None
        self.popularity = None
        self.profile_path = None
        self.profile_url = None
        self.images = None
        self.credits_cast = None
        self.credits_crew = None
        self.notable_works = None

    async def load_data(self):
        """Populates instance attributes with data received from TMDB API"""
        r = await tmdb_get(f'/person/{self.id}', append_to_response='combined_credits,images,external_ids')
        self.imdb_id = r['imdb_id']
        self.name = r['name']
        self.biography = r['biography']
        self.short_bio = trim_by_paragraph(self.biography)
        self.birthday = dt.datetime.strptime(r['birthday'], '%Y-%m-%d').date() if r['birthday'] else None
        self.place_of_birth = r['place_of_birth']
        self.deathday = dt.datetime.strptime(r['deathday'], '%Y-%m-%d').date() if r['deathday'] else None
        self.age = calculate_age(self.birthday, self.deathday) if self.birthday else None
        self.gender = r['gender']
        self.homepage = r['homepage']
        self.known_for_department = r['known_for_department']
        self.popularity = r['popularity']
        self.profile_path = r['profile_path']
        self.profile_url = f'{TMDB_WEB_BASE_URL}/person/{self.id}'
        self.images = [profile['file_path'] for profile in r['images']['profiles']]
        combined_credits = standardize_credits(r['combined_credits'])
        self.credits_cast = combined_credits['cast']
        self.credits_crew = combined_credits['crew']
        self.notable_works = self._build_notable_works()

    def _build_notable_works(self):
        """
        Creates a string of the person's notable works from most voted productions in their known-for department.
        Will be deprecated once TMDB API provides it as a field in the /person/id endpoint.
        """
        if self.known_for_department == 'Acting':
            works = [c for c in sorted(self.credits_cast, key=lambda x: x['vote_count'], reverse=True)][:5]
        else:
            works = [c for c in sorted(self.credits_crew, key=lambda x: x['vote_count'], reverse=True) if
                     c['department'] == self.known_for_department][:5]

        notable_works = ''
        for w in works:
            year = w['release_date'].partition('-')[0]
            url = f"{TMDB_WEB_BASE_URL}/{w['media_type']}/{w['id']}"
            notable_works += f"[{w['title']} ({year})]({url})" + '\n'
        return notable_works

    def main_embed(self):
        """Creates the main display embed."""
        embed = discord.Embed(title=self.name,
                              description=self.short_bio if self.short_bio else 'No biography.',
                              url=self.profile_url,
                              color=COLOR_EMBED_DARK)
        embed.set_author(name='MAIN PAGE')
        if self.profile_path:
            embed.set_thumbnail(url=TMDB_IMAGE_BASE_URL + TMDB_PROFILE_SIZES[-1] + self.profile_path)

        if self.birthday and not self.deathday:
            birth = f'{self.birthday}\n({self.age} years old)'
        elif self.birthday:
            birth = self.birthday
        else:
            birth = '-'

        if self.birthday and self.deathday:
            death = f'{self.deathday}\n({self.age} years old)'
        elif self.deathday:
            death = self.deathday
        else:
            death = '-'

        embed.add_field(name='Birth', value=birth)
        embed.add_field(name='Birthplace', value=self.place_of_birth if self.place_of_birth else '-')
        embed.add_field(name='Death', value=death)
        embed.add_field(name='Notable works', value=self.notable_works if self.notable_works else '-', inline=False)
        embed.set_footer(text=f"Known for: {self.known_for_department if self.known_for_department else '-'}")
        return embed
