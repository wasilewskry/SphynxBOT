import datetime as dt

from async_lru import alru_cache

from utils.misc import get_as_json
from utils.misc import strptime, calculate_age


class ImageConfiguration:
    """Stores information needed to construct image urls."""

    def __init__(self, **kwargs):
        self.base_url: str = kwargs.get('base_url')
        self.secure_base_url: str = kwargs.get('secure_base_url')
        self.backdrop_sizes: list[str] = kwargs.get('backdrop_sizes')
        self.logo_sizes: list[str] = kwargs.get('logo_sizes')
        self.poster_sizes: list[str] = kwargs.get('poster_sizes')
        self.profile_sizes: list[str] = kwargs.get('profile_sizes')
        self.still_sizes: list[str] = kwargs.get('still_sizes')


class Credit:
    """
    Represents a credit for a movie or a show.
    Unlike the API, this object merges credits for the same production but different characters/jobs.
    """

    def __init__(self, **kwargs):
        self.credit_type: str = kwargs.get('credit_type')
        self.media_type: str = kwargs.get('media_type')
        # Cast
        self.characters: list[str] = kwargs.get('characters', [])
        # Crew
        self.jobs: list[str] = kwargs.get('jobs', [])
        # Movie
        self.video: bool = kwargs.get('video')
        # TV
        self.episode_counts: dict[str, int] = kwargs.get('episode_counts', {})
        self.origin_country: list[str] = kwargs.get('origin_country')
        # Unified
        self.original_title: str = kwargs.get('original_title', kwargs.get('original_name'))
        self.title: str = kwargs.get('title', kwargs.get('name'))
        self.release_date: dt.date = strptime(kwargs.get('release_date', kwargs.get('first_air_date')), '%Y-%m-%d',
                                              no_time=True)
        # Shared
        self.department: str = kwargs.get('department')
        self.adult: bool = kwargs.get('adult')
        self.backdrop_path: str = kwargs.get('backdrop_path')
        self.genre_ids: list[int] = kwargs.get('genre_ids')
        self.id: int = kwargs.get('id')
        self.original_language: str = kwargs.get('original_language')
        self.overview: str = kwargs.get('overview')
        self.popularity: float = kwargs.get('popularity')
        self.poster_path: str = kwargs.get('poster_path')
        self.vote_average: float = kwargs.get('vote_average')
        self.vote_count: int = kwargs.get('vote_count')
        self.credit_id: str = kwargs.get('credit_id')
        self.web_url = f'{TmdbClient.base_web_url}/{self.media_type}/{self.id}'

    def __eq__(self, other):
        return self.media_type == other.media_type and self.id == other.id and self.department == other.department

    def __lt__(self, other):
        if self.release_date and other.release_date:
            return self.release_date < other.release_date
        # Since productions with no specified date are usually upcoming, those with specified date are considered older
        elif self.release_date:
            return True
        else:
            return False

    def __str__(self):
        if self.release_date:
            s = f'``{self.release_date.year}``'
        else:
            s = '``----``'
        if self.media_type == 'movie':
            s += f' \U0001F3A5 '  # 🎥
        else:
            s += f' \U0001F4FA '  # 📺
        s += f'[{self.title}]({TmdbClient.base_web_url}/{self.media_type}/{self.id})'
        if self.characters:
            with_episodes = self._with_episodes(self.characters)
            s += ' as ' + ', '.join(with_episodes)
        elif self.jobs:
            with_episodes = self._with_episodes(self.jobs)
            s += ' ... ' + ', '.join(with_episodes)
        return s

    def _with_episodes(self, characters_or_jobs: list[str]):
        """Returns a list of character/job strings with the amount of episodes appended to them (if any)."""
        with_episodes = []
        for c_or_j in characters_or_jobs:
            if episode_count := self.episode_counts.get(c_or_j):
                with_episodes.append(c_or_j + f' **({episode_count} episode{"s" if episode_count > 1 else ""})**')
            else:
                with_episodes.append(c_or_j)
        return with_episodes


class Image:
    """Represents an image on TMDB."""

    def __init__(self, **kwargs):
        self.image_type: str = kwargs.get('image_type')
        self.aspect_ratio: float = kwargs.get('aspect_ratio')
        self.height: int = kwargs.get('height')
        self.file_path: str = kwargs.get('file_path')
        self.vote_average: float = kwargs.get('vote_average')
        self.vote_count: int = kwargs.get('vote_count')
        self.width: int = kwargs.get('width')


class ExternalIds:
    """Stores ids for external services."""

    def __init__(self, **kwargs):
        self.freebase_mid: str = kwargs.get('freebase_mid')
        self.freebase_id: str = kwargs.get('freebase_id')
        self.imdb_id: str = kwargs.get('imdb_id')
        self.tvrage_id: int = kwargs.get('tvrage_id')
        self.wikidata_id: str = kwargs.get('wikidata_id')
        self.facebook_id: str = kwargs.get('facebook_id')
        self.instagram_id: str = kwargs.get('instagram_id')
        self.twitter_id: str = kwargs.get('twitter_id')


class Person:
    """Represents a person on TMDB"""

    def __init__(self, **kwargs):
        self.adult: bool = kwargs.get('adult')
        self.also_known_as: list[str] = kwargs.get('also_known_as')
        self.biography: str = kwargs.get('biography')
        self.birthday: dt.date = strptime(kwargs.get('birthday'), '%Y-%m-%d', no_time=True)
        self.deathday: dt.date = strptime(kwargs.get('deathday'), '%Y-%m-%d', no_time=True)
        self.gender: int = kwargs.get('gender')
        self.homepage: str = kwargs.get('homepage')
        self.id: int = kwargs.get('id')
        self.imdb_id: str = kwargs.get('imdb_id')
        self.known_for_department: str = kwargs.get('known_for_department')
        self.name: str = kwargs.get('name')
        self.place_of_birth: str = kwargs.get('place_of_birth')
        self.popularity: float = kwargs.get('popularity')
        self.profile_path: str = kwargs.get('profile_path')
        self.credits: list[Credit] = kwargs.get('credits')
        self.images: list[Image] = kwargs.get('images')
        self.external_ids: ExternalIds = kwargs.get('external_ids')
        self.web_url = f'{TmdbClient.base_web_url}/person/{self.id}'
        self.age = calculate_age(self.birthday, self.deathday) if self.birthday else None
        self.notable_credits = self._get_notable_credits() if self.credits else None

    def _get_notable_credits(self, count: int = 5) -> list[Credit]:
        return [c for c in sorted(self.credits, key=lambda x: x.vote_count, reverse=True) if
                c.department == self.known_for_department][:count]


class TmdbClient:
    """TMDB client class used for sending requests to the API."""
    base_api_url = 'https://api.themoviedb.org/3'
    base_web_url = 'https://www.themoviedb.org'

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.img_config: ImageConfiguration | None = None

    async def _get(self, endpoint: str, **kwargs):
        """Creates a request to a given endpoint. Accepts query parameters as keyword arguments."""
        url = f'{self.base_api_url}{endpoint}?api_key={self.api_key}'
        for k, v in kwargs.items():
            url += f'&{k}={v}'
        return await get_as_json(url)

    @alru_cache(maxsize=1)
    async def update_image_configuration(self):
        """Updates image configuration attribute in class instance."""
        parsed = await self._get('/configuration')
        image_config = parsed['images']
        self.img_config = ImageConfiguration(**image_config)

    async def get_person(self, person_id: int) -> Person:
        """GET request for specified person."""
        parsed = await self._get(f'/person/{person_id}', append_to_response='combined_credits,images,external_ids')
        combined_credits = parsed.pop('combined_credits')
        objectified_credits = []
        for credit_type in ['cast', 'crew']:
            for credit in combined_credits[credit_type]:
                try:
                    episode_count = credit.pop('episode_count')
                except KeyError:
                    episode_count = None
                obj = Credit(**credit)
                obj.credit_type = credit_type
                if credit_type == 'crew':
                    attr = 'jobs'
                    credited_for = credit['job']
                else:
                    obj.department = 'Acting'
                    attr = 'characters'
                    credited_for = credit['character']
                if obj in objectified_credits:
                    if credited_for:
                        idx = objectified_credits.index(obj)
                        getattr(objectified_credits[idx], attr).append(credited_for)
                        getattr(objectified_credits[idx], 'episode_counts')[credited_for] = episode_count
                else:
                    if credited_for:
                        getattr(obj, attr).append(credited_for)
                        getattr(obj, 'episode_counts')[credited_for] = episode_count
                    objectified_credits.append(obj)
        parsed['credits'] = objectified_credits
        images = parsed.pop('images')
        objectified_images = []
        for image in images['profiles']:
            obj = Image(**image)
            obj.image_type = 'profile'
            objectified_images.append(obj)
        parsed['images'] = objectified_images
        parsed['external_ids'] = ExternalIds(**parsed['external_ids'])
        return Person(**parsed)

    async def query_person(self, query: str) -> list[Person]:
        """GET request used to search for people based on user query."""
        parsed = await self._get(f'/search/person', query=query)
        return [Person(**kwargs) for kwargs in parsed['results']]
