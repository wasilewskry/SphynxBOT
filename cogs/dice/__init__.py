from run import Sphynx
from .cog import DiceCog


async def setup(bot: Sphynx):
    await bot.add_cog(DiceCog(bot))
