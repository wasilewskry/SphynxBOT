from typing import List

import discord
from discord import app_commands
from discord.ext import commands

from cogs.helper.cinema_helper import Person, tmdb_get
from cogs.helper.views import CinemaPersonView


async def person_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    page = await tmdb_get('/search/person', query=current)
    if not current:
        return []
    results = sorted(page['results'], key=lambda x: x['popularity'], reverse=True)[:25]
    dupes = {}
    for r in results:
        k = r['name']
        dupes[k] = dupes.get(k, 0) + 1
        if dupes[k] > 1:
            r['name'] += f" ({dupes[k]})"
    return [app_commands.Choice(name=r['name'] + ' (1)' if dupes.get(r['name'], 0) > 1 else r['name'], value=r['id'])
            for r in results]


class Cinema(commands.GroupCog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    @app_commands.command()
    async def test(self, interaction: discord.Interaction):
        ...

    @app_commands.command()
    @app_commands.rename(person_id='name')
    @app_commands.autocomplete(person_id=person_autocomplete)
    @app_commands.describe(person_id='Name of the person you want to look up')
    async def person(self, interaction: discord.Interaction, person_id: int):
        """Displays personal details"""
        person = Person(person_id)
        await person.load_data()
        embed = person.main_embed()
        await interaction.response.send_message(embed=embed, view=CinemaPersonView(person))


# -------------------------------------------------------------------------------------------------------------------- #
async def setup(bot: commands.Bot):
    await bot.add_cog(Cinema(bot))
