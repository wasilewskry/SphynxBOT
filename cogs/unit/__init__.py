from run import Sphynx
from .cog import UnitCog


async def setup(bot: Sphynx):
    await bot.add_cog(UnitCog(bot))
