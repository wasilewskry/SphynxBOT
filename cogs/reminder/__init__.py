from run import Sphynx
from .cog import ReminderCog


async def setup(bot: Sphynx):
    await bot.add_cog(ReminderCog(bot))
