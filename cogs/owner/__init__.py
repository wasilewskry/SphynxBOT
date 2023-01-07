from run import Sphynx
from .cog import OwnerCog


async def setup(bot: Sphynx):
    await bot.add_cog(OwnerCog(bot))
