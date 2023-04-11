import logging
import os

from run import Sphynx
from .cog import CinemaCog
from .models import TmdbClient

_log = logging.getLogger(__name__)


async def setup(bot: Sphynx):
    env_var = 'SPHYNX_TMDB_API_KEY'
    try:
        tmdb_api_key = os.environ[env_var]
    except KeyError:
        _log.warning(f'"{env_var}" environment variable not set: Cinema cog will not be available.')
        return
    tmdb_client = TmdbClient(tmdb_api_key)
    await tmdb_client.update_configuration()
    _log.info('Retrieved configuration from TMDB.')
    await bot.add_cog(CinemaCog(bot, tmdb_client))
