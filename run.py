from glob import glob

import discord
from discord.ext import commands
from tortoise import Tortoise

from config import token, db_url


class Sphynx(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned,
                         intents=discord.Intents.all())

        self.initial_extensions = [
            'cogs.owner',
            'cogs.unit',
            'cogs.reminder',
            'cogs.cinema'
        ]

    async def setup_hook(self):
        models = ['cogs.shared_models']
        models += [path.replace('.py', '').replace('\\', '/').replace('/', '.') for path in glob('cogs/*/models.py')]
        await Tortoise.init(
            db_url=db_url,
            modules={'models': models})
        await Tortoise.generate_schemas()
        for ext in self.initial_extensions:
            await self.load_extension(ext)


# -------------------------------------------------------------------------------------------------------------------- #
if __name__ == '__main__':
    sphynx = Sphynx()
    sphynx.run(token, root_logger=True)
