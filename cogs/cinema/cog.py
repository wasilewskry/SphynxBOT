import collections

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from run import Sphynx
from .models import TmdbClient
from .views import PersonView


class CinemaCog(commands.GroupCog, group_name='cinema'):
    def __init__(self, bot: Sphynx, tmdb_client: TmdbClient):
        self.bot = bot
        self.tmdb_client = tmdb_client

    @app_commands.command()
    async def test(self, interaction: discord.Interaction):
        ...

    @app_commands.command()
    @app_commands.rename(person_id='name')
    @app_commands.describe(person_id='Name of the person you want to look up')
    async def person(self, interaction: discord.Interaction, person_id: int):
        """Displays personal details"""
        person = await self.tmdb_client.get_person(person_id)
        view = PersonView(person, self.tmdb_client)
        embed = view.main_embed()
        await interaction.response.send_message(view=view, embed=embed)

    @person.autocomplete('person_id')
    async def person_autocomplete(self, interaction: discord.Interaction, current: str) -> list[Choice[int]]:
        """Autocompletes `person_id` by pulling suggestions from TMDB API and displaying them as the person's name."""
        if not current:
            return []
        candidates = await self.tmdb_client.query_person(current)
        candidates = sorted(candidates, key=lambda x: x.popularity, reverse=True)[:25]
        dupes = collections.defaultdict(int)
        for c in candidates:
            name = c.name
            dupes[name] += 1
            if dupes[name] > 1:
                c.name += f" ({dupes[name]})"
        return [app_commands.Choice(name=c.name + ' (1)' if dupes.get(c.name, 0) > 1 else c.name, value=c.id)
                for c in candidates]
