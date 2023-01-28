import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from run import Sphynx
from .helpers import deduplicate_autocomplete_labels, prepare_production_autocomplete_choices, CinemaEntity
from .models import TmdbClient, TmdbApiException
from .views import PersonView, MovieView, TvView, SimplePersonPagingView, MoviePagingView, TvPagingView


class CinemaCog(commands.GroupCog, group_name='cinema'):
    def __init__(self, bot: Sphynx, tmdb_client: TmdbClient):
        self.bot = bot
        self.tmdb_client = tmdb_client

    @app_commands.command()
    @app_commands.rename(movie_id='name')
    @app_commands.describe(movie_id='Name of the movie you want to look up')
    async def movie(self, interaction: discord.Interaction, movie_id: int):
        """Displays movie details."""
        try:
            movie = await self.tmdb_client.get_movie(movie_id)
        except TmdbApiException:
            await interaction.response.send_message('Invalid choice.', ephemeral=True)
            return
        view = MovieView(movie, self.tmdb_client)
        embed = view.main_embed()
        await interaction.response.send_message(view=view, embed=embed)

    @movie.autocomplete('movie_id')
    async def movie_autocomplete(self, interaction: discord.Interaction, current: str) -> list[Choice[int]]:
        """Autocompletes `movie_id` by pulling suggestions from TMDB API and displaying them as the movie's title."""
        if not current:
            return []
        candidates = await self.tmdb_client.query_movie(current)
        choices = prepare_production_autocomplete_choices(candidates)
        return choices[:25]

    @app_commands.command()
    @app_commands.rename(tv_id='name')
    @app_commands.describe(tv_id='Name of the show you want to look up')
    async def tv(self, interaction: discord.Interaction, tv_id: int):
        """Displays tv details."""
        try:
            tv = await self.tmdb_client.get_tv(tv_id)
        except TmdbApiException:
            await interaction.response.send_message('Invalid choice.', ephemeral=True)
            return
        view = TvView(tv, self.tmdb_client)
        embed = view.main_embed()
        await interaction.response.send_message(view=view, embed=embed)

    @tv.autocomplete('tv_id')
    async def tv_autocomplete(self, interaction: discord.Interaction, current: str) -> list[Choice[int]]:
        """Autocompletes `tv_id` by pulling suggestions from TMDB API and displaying them as the show's title."""
        if not current:
            return []
        candidates = await self.tmdb_client.query_tv(current)
        choices = prepare_production_autocomplete_choices(candidates)
        return choices[:25]

    @app_commands.command()
    @app_commands.rename(person_id='name')
    @app_commands.describe(person_id='Name of the person you want to look up')
    async def person(self, interaction: discord.Interaction, person_id: int):
        """Displays personal details."""
        try:
            person = await self.tmdb_client.get_person(person_id)
        except TmdbApiException:
            await interaction.response.send_message('Invalid choice.', ephemeral=True)
            return
        view = PersonView(person, self.tmdb_client)
        embed = view.main_embed()
        await interaction.response.send_message(view=view, embed=embed)

    @person.autocomplete('person_id')
    async def person_autocomplete(self, interaction: discord.Interaction, current: str) -> list[Choice[int]]:
        """Autocompletes `person_id` by pulling suggestions from TMDB API and displaying them as the person's name."""
        if not current:
            return []
        candidates = await self.tmdb_client.query_person(current)
        candidates = sorted(candidates, key=lambda x: x.popularity, reverse=True)
        choices = [app_commands.Choice(name=f'{c.name}', value=c.id) for c in candidates]
        choices = deduplicate_autocomplete_labels(choices)
        return choices[:25]

    @app_commands.command()
    @app_commands.describe(entity='Type of currently popular cinema-related object you want to list')
    async def popular(self, interaction: discord.Interaction, entity: CinemaEntity):
        """Displays currently popular entities."""
        if entity == CinemaEntity.person:
            people = await self.tmdb_client.get_popular_people()
            view = SimplePersonPagingView(people, self.tmdb_client)
            embed = view.person_list_embed()
            await interaction.response.send_message(view=view, embed=embed)
        elif entity == CinemaEntity.movie:
            movies = await self.tmdb_client.get_popular_movies()
            view = MoviePagingView(movies, self.tmdb_client)
            embed = view.movie_list_embed()
            await interaction.response.send_message(view=view, embed=embed)
        else:
            tv = await self.tmdb_client.get_popular_tv()
            view = TvPagingView(tv, self.tmdb_client)
            embed = view.tv_list_embed()
            await interaction.response.send_message(view=view, embed=embed)
