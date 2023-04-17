import datetime as dt
from copy import deepcopy

from async_lru import alru_cache

from utils.misc import get_as_json
from utils.misc import strptime, calculate_age


class TmdbApiException(Exception):
    pass


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
    def __init__(self, **kwargs):
        self.credit_type: str = kwargs.get('credit_type')
        self.media_type: str = kwargs.get('media_type')
        self.credit_subject: str = kwargs.get('title', kwargs.get('name'))
        self.department: str = kwargs.get('department')
        self.characters: list[str] = kwargs.get('characters', [])
        self.jobs: list[str] = kwargs.get('jobs', [])
        self.order: int = kwargs.get('order')
        self.id: int = kwargs.get('id')
        self.gender: int = kwargs.get('gender')
        self.release_date: dt.date = strptime(kwargs.get('release_date', kwargs.get('first_air_date')),
                                              '%Y-%m-%d',
                                              no_time=True)
        self.episode_counts: dict[str, int] = kwargs.get('episode_counts', {})
        self.vote_count: int = kwargs.get('vote_count')
        self.web_url = f'{TmdbClient.base_web_url}/{self.media_type if self.media_type else "person"}/{self.id}'

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
        if self.media_type:
            s = self._production_string()
        else:
            s = self._person_string()

        s += f'[{self.credit_subject}]({self.web_url})'
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

    def _production_string(self):
        if self.release_date:
            s = f'``{self.release_date.year}``'
        else:
            s = '``----``'
        if self.media_type == 'movie':
            s += ' \U0001F3A5 '  # 🎥
        else:
            s += ' \U0001F4FA '  # 📺
        return s

    def _person_string(self):
        if self.gender == 1:
            s = '\U00002640 '  # ♀️
        elif self.gender == 2:
            s = '\U00002642 '  # ♂️
        elif self.gender == 3:
            s = '\U000026A7 '  # ⚧
        else:
            s = '\U00002754 '  # ❔
        return s


class Image:
    """Represents an image on TMDB."""

    def __init__(self, **kwargs):
        self.image_category: str = kwargs.get('image_category')
        self.aspect_ratio: float = kwargs.get('aspect_ratio')
        self.height: int = kwargs.get('height')
        self.iso_639_1: str = kwargs.get('iso_639_1')
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
        self.known_for: list[Production] = kwargs.get('known_for', [])
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


class Production:
    media_type = None

    def __init__(self, **kwargs):
        self.id: int = kwargs.get('id')
        self.adult: bool = kwargs.get('adult')
        self.title: str = kwargs.get('title', kwargs.get('name'))
        self.original_title: str = kwargs.get('original_title', kwargs.get('original_name'))
        self.release_date: dt.date = strptime(kwargs.get('release_date', kwargs.get('first_air_date')), '%Y-%m-%d',
                                              no_time=True)
        self.backdrop_path: str = kwargs.get('backdrop_path')
        self.poster_path: str = kwargs.get('poster_path')
        self.overview: str = kwargs.get('overview')
        self.original_language: str = kwargs.get('original_language')
        self.popularity: float = kwargs.get('popularity')
        self.tagline: str = kwargs.get('tagline')
        self.genres: list[str] = kwargs.get('genres')
        self.genre_ids: list[int] = kwargs.get('genre_ids')
        self.homepage: str = kwargs.get('homepage')
        self.status: str = kwargs.get('status')
        self.vote_average: float = kwargs.get('vote_average')
        self.vote_count: float = kwargs.get('vote_count')
        self.spoken_languages: list[str] = kwargs.get('spoken_languages')
        self.images: list[Image] = kwargs.get('images')
        self.external_ids: ExternalIds = kwargs.get('external_ids')
        self.keywords: list[str] = kwargs.get('keywords')
        self.credits: list[Credit] = kwargs.get('credits', [])
        # self.production_companies: ??? = kwargs.get('production_companies')
        # self.production_countries: ??? = kwargs.get('production_countries')
        self.web_url = f'{TmdbClient.base_web_url}/{self.media_type}/{self.id}'
        self.similar: list[Production] = kwargs.get('similar')
        self.recommendations: list[Production] = kwargs.get('recommendations')

    def pretty_score(self):
        return f'{int(self.vote_average * 10)}%'


class Movie(Production):
    media_type = 'movie'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.budget: int = kwargs.get('budget')
        self.revenue: int = kwargs.get('revenue')
        self.runtime: int = kwargs.get('runtime')
        self.video: bool = kwargs.get('video')
        # self.belongs_to_collection: ??? = kwargs.get('belongs_to_collection')

    def pretty_runtime(self):
        if not self.runtime:
            return '-'
        hours = self.runtime // 60
        minutes = self.runtime % 60
        return f"{(str(hours) + 'h ') if hours else ''}{str(minutes) + 'm'}"


class Tv(Production):
    media_type = 'tv'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.episode_run_time: list[int] = kwargs.get('episode_run_time')
        self.last_air_date: dt.date = strptime(kwargs.get('last_air_date'), '%Y-%m-%d', no_time=True)
        self.created_by: list[Person] = kwargs.get('created_by')
        self.in_production: bool = kwargs.get('in_production')
        self.languages: list[str] = kwargs.get('languages')
        # self.last_episode_to_air: ??? = kwargs.get('last_episode_to_air')
        # self.next_episode_to_air: ??? = kwargs.get('next_episode_to_air')
        self.networks: list[str] = kwargs.get('networks')
        self.number_of_episodes: int = kwargs.get('number_of_episodes')
        self.number_of_seasons: int = kwargs.get('number_of_seasons')
        self.origin_country: list[str] = kwargs.get('origin_country')
        # self.seasons: ??? = kwargs.get('seasons')
        self.type: str = kwargs.get('type')

    def pretty_runtime(self):
        if not self.episode_run_time:
            return '-'
        runtime = self.episode_run_time[0]  # For some reason there's never more than 1 value
        hours = runtime // 60
        minutes = runtime % 60
        return f"{(str(hours) + 'h ') if hours else ''}{str(minutes) + 'm'}"


class TmdbClient:
    """TMDB client class used for sending requests to the API."""
    base_api_url = 'https://api.themoviedb.org/3'
    base_web_url = 'https://www.themoviedb.org'

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.img_config: ImageConfiguration | None = None
        self.language_config: dict[str, str] = {}
        self.movie_genres: dict[int, str] = {}
        self.tv_genres: dict[int, str] = {}

    async def _get(self, endpoint: str, **kwargs):
        """Creates a request to a given endpoint. Accepts query parameters as keyword arguments."""
        # As of December 16, 2019, TMDB has disabled the API rate limiting.
        url = f'{self.base_api_url}{endpoint}?api_key={self.api_key}'
        for k, v in kwargs.items():
            url += f'&{k}={v}'
        response = await get_as_json(url)
        if type(response) == dict and response.get('status_code') == 34:
            raise TmdbApiException(response)
        return await get_as_json(url)

    @alru_cache(maxsize=1)
    async def update_configuration(self):
        """Updates image configuration attribute in class instance."""
        parsed = await self._get('/configuration')
        image_config = parsed['images']
        self.img_config = ImageConfiguration(**image_config)
        parsed = await self._get('/configuration/languages')
        for conf in parsed:
            self.language_config[conf['iso_639_1']] = conf['english_name']
        parsed = await self._get('/genre/movie/list')
        for genre in parsed['genres']:
            self.movie_genres[genre['id']] = genre['name']
        parsed = await self._get('/genre/tv/list')
        for genre in parsed['genres']:
            self.tv_genres[genre['id']] = genre['name']

    def _process_credits(self, combined_credits: dict[str, list[dict]]) -> list[Credit]:
        # TODO: Rewrite this entire method
        objectified_credits = []
        for credit_type in ['cast', 'crew']:
            for credit in combined_credits[credit_type]:
                if credit_type == 'cast':
                    credit['department'] = 'Acting'
                try:
                    episode_count = credit.pop('episode_count')
                except KeyError:
                    episode_count = None
                try:
                    credit['jobs_'] = credit.pop('jobs')
                except KeyError:
                    pass
                obj = Credit(**credit)
                obj.credit_type = credit_type
                if not (credit.get('roles') or credit.get('jobs_')):
                    if credit_type == 'crew':
                        attr = 'jobs'
                        credited_for = credit['job']
                    else:
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
                else:
                    if roles := credit.get('roles'):
                        for role in roles:
                            obj.characters.append(role['character'])
                            obj.episode_counts[role['character']] = role['episode_count']
                    if jobs := credit.get('jobs_'):
                        for job in jobs:
                            obj.jobs.append(job['job'])
                            obj.episode_counts[job['job']] = job['episode_count']
                    objectified_credits.append(obj)
        return objectified_credits

    def _process_images(self, images: dict[str, list[dict]]) -> list[Image]:
        objectified_images = []
        for category, image_list in images.items():
            for img in image_list:
                obj = Image(**img)
                obj.image_category = category
                objectified_images.append(obj)
        return objectified_images

    async def get_person(self, person_id: int) -> Person:
        """GET request for specified person."""
        parsed = await self._get(f'/person/{person_id}', append_to_response='combined_credits,images,external_ids')
        combined_credits = parsed.pop('combined_credits')
        parsed['credits'] = self._process_credits(combined_credits)
        parsed['images'] = self._process_images(parsed['images'])
        parsed['external_ids'] = ExternalIds(**parsed['external_ids'])
        return Person(**parsed)

    def _prepare_production(self, parsed_production: dict):
        parsed = deepcopy(parsed_production)
        parsed['genres'] = [genre['name'] for genre in parsed['genres']]
        parsed['spoken_languages'] = [self.language_config[lang['iso_639_1']] for lang in parsed['spoken_languages']]
        parsed['images'] = self._process_images(parsed['images'])
        parsed['external_ids'] = ExternalIds(**parsed['external_ids'])
        return parsed

    async def get_movie(self, movie_id: int) -> Movie:
        parsed = await self._get(f'/movie/{movie_id}', append_to_response='alternative_titles,credits,'
                                                                          'external_ids,images,keywords,'
                                                                          'recommendations,release_dates,'
                                                                          'similar,videos')
        parsed = self._prepare_production(parsed)
        parsed['keywords'] = [keyword['name'] for keyword in parsed['keywords']['keywords']]
        parsed['credits'] = self._process_credits(parsed['credits'])
        parsed['similar'] = [Movie(**kwargs) for kwargs in parsed['similar']['results']]
        parsed['recommendations'] = [Movie(**kwargs) for kwargs in parsed['recommendations']['results']]
        return Movie(**parsed)

    async def get_tv(self, tv_id: int) -> Tv:
        parsed = await self._get(f'/tv/{tv_id}', append_to_response='aggregate_credits,alternative_titles,'
                                                                    'content_ratings,external_ids,images,'
                                                                    'keywords,recommendations,'
                                                                    'screened_theatrically,similar,videos')
        parsed = self._prepare_production(parsed)
        parsed['created_by'] = [Person(**person) for person in parsed['created_by']]
        parsed['networks'] = [network['name'] for network in parsed['networks']]
        parsed['keywords'] = [keyword['name'] for keyword in parsed['keywords']['results']]
        parsed['credits'] = self._process_credits(parsed['aggregate_credits'])
        parsed['similar'] = [Tv(**kwargs) for kwargs in parsed['similar']['results']]
        parsed['recommendations'] = [Tv(**kwargs) for kwargs in parsed['recommendations']['results']]
        return Tv(**parsed)

    async def get_popular_people(self):
        parsed = await self._get(f'/person/popular')
        parsed = parsed['results']
        for person in parsed:
            person['known_for'] = [Tv(**kwargs) if kwargs['media_type'] == 'tv' else Movie(**kwargs)
                                   for kwargs in person['known_for']]
        return [Person(**kwargs) for kwargs in parsed]

    async def get_popular_movies(self):
        parsed = await self._get(f'/movie/popular')
        parsed = parsed['results']
        return [Movie(**kwargs) for kwargs in parsed]

    async def get_popular_tv(self):
        parsed = await self._get(f'/tv/popular')
        parsed = parsed['results']
        return [Tv(**kwargs) for kwargs in parsed]

    async def query_person(self, query: str) -> list[Person]:
        """GET request used to search for people based on user query."""
        parsed = await self._get(f'/search/person', query=query)
        return [Person(**kwargs) for kwargs in parsed['results']]

    async def query_movie(self, query: str) -> list[Movie]:
        """GET request used to search for movies based on user query."""
        parsed = await self._get(f'/search/movie', query=query)
        return [Movie(**kwargs) for kwargs in parsed['results']]

    async def query_tv(self, query: str) -> list[Tv]:
        """GET request used to search for shows based on user query."""
        parsed = await self._get(f'/search/tv', query=query)
        return [Tv(**kwargs) for kwargs in parsed['results']]
