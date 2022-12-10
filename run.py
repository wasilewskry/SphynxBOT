import discord
from discord.ext import commands
from config import token


class Sphynx(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned,
                         intents=discord.Intents.all())

        self.initial_extensions = [
            'cogs.owner',
            'cogs.unit',
        ]

    async def setup_hook(self):
        for ext in self.initial_extensions:
            await self.load_extension(ext)


# -------------------------------------------------------------------------------------------------------------------- #
if __name__ == '__main__':
    bingus = Sphynx()
    bingus.run(token)
