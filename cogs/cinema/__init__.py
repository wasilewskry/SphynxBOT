import logging

from config import tmdb_api_key
from run import Sphynx
from .cog import CinemaCog
from .models import TmdbClient

_log = logging.getLogger(__name__)


async def setup(bot: Sphynx):
    tmdb_client = TmdbClient(tmdb_api_key)
    await tmdb_client.update_configuration()
    _log.info('retrieved configuration from TMDB')
    await bot.add_cog(CinemaCog(bot, tmdb_client))
