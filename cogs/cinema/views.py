import collections

import discord

from utils.constants import EMBED_DESC_MAX_LENGTH, COLOR_EMBED_DARK
from utils.misc import trim_by_paragraph
from .helpers import verbose_date
from .models import Person, TmdbClient, Movie, Production, Tv
from ..shared_views import SphynxView, PaginatingView


class PersonView(SphynxView):
    """Primary view displayed when looking up a person."""

    def __init__(
            self,
            interaction: discord.Interaction,
            person: Person,
            client: TmdbClient,
            **kwargs
    ):
        super().__init__(interaction, **kwargs)
        self.person = person
        self.client = client
        self.short_bio = trim_by_paragraph(self.person.biography, EMBED_DESC_MAX_LENGTH // 4)
        if self.person.notable_credits:
            self.stringified_notable_credits = '\n'.join(
                [f'[{c.credit_subject} ({c.release_date.year})]({c.web_url})' for c in self.person.notable_credits])
        if self.person.images:
            self.images.disabled = False
        if self.person.biography != self.short_bio:
            self.biography.disabled = False
        if self.person.credits:
            self.credits.disabled = False

    def _paginate_bio(self, page_length: int = EMBED_DESC_MAX_LENGTH // 2) -> list[str]:
        """Splits biography into pages."""
        sentences = self.person.biography.split('.')
        pages = []
        page = ''
        if sentences[-1] == '':
            sentences = sentences[:-1]
        for sentence in sentences:
            if len(page) + len(sentence) + 1 < page_length:
                page += sentence + '.'
            else:
                pages.append(page)
                page = sentence + '.'
        pages.append(page)
        return pages

    def _paginate_credits(self, credits_per_page: int = 20) -> dict[str, list[str]]:
        """Turns credits into strings for display and splits them into lists of pages for every category."""
        pages = collections.defaultdict(list)
        for credit in sorted(self.person.credits, reverse=True):
            pages[credit.department].append(credit)
        for department, dep_credits in pages.items():
            pages[department] = ['\n'.join(str(credit) for credit in dep_credits[x:x + credits_per_page])
                                 for x in range(0, len(dep_credits), credits_per_page)]
        return pages

    def embed(self) -> discord.Embed:
        """Returns the embed used for displaying the person's primary information."""
        embed = discord.Embed(title=self.person.name,
                              description=self.short_bio if self.short_bio else 'No biography.',
                              url=self.person.web_url,
                              color=COLOR_EMBED_DARK)
        embed.set_author(name='MAIN PAGE')
        if self.person.profile_path:
            img_config = self.client.img_config
            url = img_config.secure_base_url + img_config.profile_sizes[-1] + self.person.profile_path
            embed.set_thumbnail(url=url)
        if self.person.birthday and not self.person.deathday:
            birth = f'{self.person.birthday}\n({self.person.age} years old)'
        elif self.person.birthday:
            birth = self.person.birthday
        else:
            birth = '-'
        if self.person.birthday and self.person.deathday:
            death = f'{self.person.deathday}\n({self.person.age} years old)'
        elif self.person.deathday:
            death = self.person.deathday
        else:
            death = '-'
        embed.add_field(name='Birth', value=birth)
        embed.add_field(name='Birthplace', value=self.person.place_of_birth if self.person.place_of_birth else '-')
        embed.add_field(name='Death', value=death)
        embed.add_field(
            name='Notable productions',
            value=self.stringified_notable_credits if self.person.notable_credits else '-',
            inline=False
        )
        embed.set_footer(
            text=f"Known for: {self.person.known_for_department if self.person.known_for_department else '-'}"
        )
        return embed

    @discord.ui.button(label='FULL BIO', style=discord.ButtonStyle.gray, disabled=True)
    async def biography(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays full biography when pressed."""
        pages = self._paginate_bio()
        view = PersonBiographyView(interaction, pages, self)
        embed = view.embed()
        await interaction.response.edit_message(view=view, embed=embed)

    @discord.ui.button(label='GALLERY', style=discord.ButtonStyle.gray, disabled=True)
    async def images(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays image gallery when pressed."""
        img_config = self.client.img_config
        pages = [
            img_config.secure_base_url + img_config.profile_sizes[-1] + img.file_path for img in self.person.images]
        view = PersonImageView(interaction, pages, self)
        embed = view.embed()
        await interaction.response.edit_message(view=view, embed=embed)

    @discord.ui.button(label='CREDITS', style=discord.ButtonStyle.gray, disabled=True)
    async def credits(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays complete credits when pressed."""
        pages = self._paginate_credits()
        view = PersonCreditsView(interaction, pages, self)
        embed = view.embed()
        await interaction.response.edit_message(view=view, embed=embed)


class ProductionView(SphynxView):
    def __init__(
            self,
            interaction: discord.Interaction,
            production: Production,
            client: TmdbClient,
            **kwargs,
    ):
        super().__init__(interaction, **kwargs)
        self.production = production
        self.client = client
        if self.production.credits:
            self.credits.disabled = False
        if self.production.similar:
            self.similar.disabled = False
        if self.production.recommendations:
            self.recommendations.disabled = False

    def _paginate_credits(self, credits_per_page: int = 20) -> dict[str, list[str]]:
        """Turns credits into strings for display and splits them into lists of pages for every category."""
        pages = collections.defaultdict(list)
        for credit in sorted(self.production.credits):
            pages[credit.department].append(credit)
        for department, dep_credits in pages.items():
            pages[department] = ['\n'.join(str(credit) for credit in dep_credits[x:x + credits_per_page])
                                 for x in range(0, len(dep_credits), credits_per_page)]
        return pages

    def _embed_description(self):
        if self.production.tagline:
            return f'**{self.production.tagline}**\n\n{self.production.overview}'
        else:
            return self.production.overview

    def _embed_title(self):
        title = self.production.title.replace('*', r'\*')
        if self.production.release_date:
            return f'{title} ({self.production.release_date.year})'
        else:
            return title

    def _base_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self._embed_title(),
            description=self._embed_description(),
            url=self.production.web_url,
            color=COLOR_EMBED_DARK
        )
        img_config = self.client.img_config
        if self.production.poster_path:
            url = img_config.secure_base_url + img_config.poster_sizes[-1] + self.production.poster_path
            embed.set_thumbnail(url=url)
        if self.production.backdrop_path:
            url = img_config.secure_base_url + img_config.backdrop_sizes[-1] + self.production.backdrop_path
            embed.set_image(url=url)
        embed.add_field(
            name='Genres',
            value=', '.join(self.production.genres) if self.production.genres else '-',
            inline=False
        )
        embed.add_field(name='Status', value=self.production.status if self.production.status else '-')
        embed.add_field(name='User score', value=self.production.pretty_score())
        if keywords := self.production.keywords:
            embed.set_footer(text=', '.join(keywords))
        return embed

    @discord.ui.button(label='CREDITS', style=discord.ButtonStyle.gray, disabled=True)
    async def credits(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays complete credits when pressed."""
        pages = self._paginate_credits()
        view = ProductionCreditsView(interaction, pages, self)
        embed = view.embed()
        await interaction.response.edit_message(view=view, embed=embed)

    @discord.ui.button(label='SIMILAR', style=discord.ButtonStyle.gray, disabled=True)
    async def similar(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays similar productions when pressed."""
        pages = [production for production in self.production.similar]
        view = ProductionSimilarView(interaction, pages, self.client, self)
        embed = view.embed()
        await interaction.response.edit_message(view=view, embed=embed)

    @discord.ui.button(label='RECOMMENDATIONS', style=discord.ButtonStyle.gray, disabled=True)
    async def recommendations(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays recommendations when pressed."""
        pages = [production for production in self.production.recommendations]
        view = ProductionRecommendationView(interaction, pages, self.client, self)
        embed = view.embed()
        await interaction.response.edit_message(view=view, embed=embed)


class MovieView(ProductionView):
    def __init__(
            self,
            interaction: discord.Interaction,
            movie: Movie,
            client: TmdbClient,
            **kwargs,
    ):
        super().__init__(interaction, movie, client, **kwargs)
        self.production = movie

    def embed(self) -> discord.Embed:
        """Returns the embed used for displaying the movie's primary information."""
        embed = self._base_embed()
        embed.add_field(name='Runtime', value=self.production.pretty_runtime())
        embed.add_field(
            name='Release date',
            value=verbose_date(self.production.release_date) if self.production.release_date else '-'
        )
        embed.add_field(name='Budget', value=f'${self.production.budget:,}' if self.production.budget else '-')
        embed.add_field(name='Revenue', value=f'${self.production.revenue:,}' if self.production.revenue else '-')
        if directors := [credit.credit_subject for credit in self.production.credits if 'Director' in credit.jobs]:
            embed.set_author(name='Directed by ' + ', '.join([director for director in directors]))
        return embed


class TvView(ProductionView):
    def __init__(
            self,
            interaction: discord.Interaction,
            tv: Tv,
            client: TmdbClient,
            **kwargs,
    ):
        super().__init__(interaction, tv, client, **kwargs)
        self.production = tv

    def embed(self) -> discord.Embed:
        """Returns the embed used for displaying the show's primary information."""
        embed = self._base_embed()
        embed.add_field(name='Episode runtime', value=self.production.pretty_runtime())
        embed.add_field(name='Type', value=self.production.type)
        embed.add_field(
            name='First aired',
            value=verbose_date(self.production.release_date) if self.production.release_date else '-'
        )
        embed.add_field(
            name='Last aired',
            value=verbose_date(self.production.last_air_date) if self.production.last_air_date else '-'
        )
        if self.production.created_by:
            embed.set_author(name='Created by ' + ', '.join([person.name for person in self.production.created_by]))
        return embed


class PersonBiographyView(PaginatingView):
    """Subview that displays the person's full biography."""

    def __init__(
            self,
            interaction: discord.Interaction,
            pages: list,
            parent_view: PersonView,
            **kwargs,
    ):
        super().__init__(interaction, pages, parent_view=parent_view, **kwargs)
        self.person = parent_view.person

    def embed(self) -> discord.Embed:
        """Creates the biography display embed."""
        embed = discord.Embed(
            title=self.person.name,
            description=self.pages[self.page_index],
            url=self.person.web_url,
            color=COLOR_EMBED_DARK)
        embed.set_author(name='FULL BIO')
        embed.set_footer(text=f'Page {self.page_index + 1}/{self.page_count}')
        return embed


class PersonImageView(PaginatingView):
    """Subview that displays the person's image gallery."""

    def __init__(
            self,
            interaction: discord.Interaction,
            pages: list,
            parent_view: PersonView,
            **kwargs
    ):
        super().__init__(interaction, pages, parent_view=parent_view, **kwargs)
        self.person = parent_view.person

    def embed(self) -> discord.Embed:
        """Creates the image display embed."""
        embed = discord.Embed(
            title=self.person.name,
            url=self.person.web_url,
            color=COLOR_EMBED_DARK)
        embed.set_image(url=self.pages[self.page_index])
        embed.set_author(name='PICTURES')
        embed.set_footer(text=f'Picture {self.page_index + 1}/{self.page_count}')
        return embed


class CreditsView(PaginatingView):
    def __init__(
            self,
            interaction: discord.Interaction,
            pages: dict[str, list],
            **kwargs
    ):
        super().__init__(interaction, pages, **kwargs)
        self.selected_category = None

    def _populate_select_menu(self):
        for department in self.pages.keys():
            if department == self.selected_category:
                self.department.append_option(discord.SelectOption(label=department, default=True))
            else:
                self.department.append_option(discord.SelectOption(label=department))

    @discord.ui.select(row=0)
    async def department(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Menu that allows the user to choose the credits department."""
        self.selected_category = select.values[0]
        self.page_index = 0
        self.page_count = len(self.pages[self.selected_category])
        self.previous_page.disabled = True
        if self.page_count == 1:
            self.next_page.disabled = True
        else:
            self.next_page.disabled = False
        for opt in select.options:
            opt.default = False
        selected_option = discord.utils.get(select.options, value=select.values[0])
        selected_option.default = True
        return await interaction.response.edit_message(
            embed=self.embed(),
            view=self,
        )


class PersonCreditsView(CreditsView):
    """Subview that displays the person's credits."""

    def __init__(
            self,
            interaction: discord.Interaction,
            pages: dict[str, list],
            parent_view: PersonView,
            **kwargs,
    ):
        super().__init__(interaction, pages, parent_view=parent_view, **kwargs)
        self.person = parent_view.person
        self.selected_category = self.person.known_for_department
        self.page_count = len(self.pages[self.selected_category])
        self._populate_select_menu()
        if self.page_count == 1:
            self.next_page.disabled = True
        else:
            self.next_page.disabled = False

    def embed(self) -> discord.Embed:
        """Creates the credits display embed."""
        embed = discord.Embed(
            title=self.person.name,
            description=self.pages[self.selected_category][self.page_index],
            url=self.person.web_url,
            color=COLOR_EMBED_DARK)
        embed.set_author(name='CREDITS')
        embed.set_footer(text=f'Page {self.page_index + 1}/{self.page_count}')
        return embed


class ProductionCreditsView(CreditsView):
    """Subview that displays the production's credits."""

    def __init__(
            self,
            interaction: discord.Interaction,
            pages: dict[str, list],
            parent_view: ProductionView,
            **kwargs,
    ):
        super().__init__(interaction, pages, parent_view=parent_view, **kwargs)
        self.production = parent_view.production
        self.selected_category = 'Acting'
        self.page_count = len(self.pages[self.selected_category])
        if self.page_count == 0:
            self.pages.pop('Acting')
            self.selected_category = sorted(self.pages, key=lambda x: len(self.pages[x]))[0]
            self.page_count = len(self.pages[self.selected_category])
        self._populate_select_menu()
        if self.page_count == 1:
            self.next_page.disabled = True
        else:
            self.next_page.disabled = False

    def embed(self) -> discord.Embed:
        """Creates the credits display embed."""
        embed = discord.Embed(
            title=self.production.title,
            description=self.pages[self.selected_category][self.page_index],
            url=self.production.web_url,
            color=COLOR_EMBED_DARK)
        embed.set_author(name='CREDITS')
        embed.set_footer(text=f'Page {self.page_index + 1}/{self.page_count}')
        return embed


class ProductionPaginatingView(PaginatingView):
    def __init__(
            self,
            interaction: discord.Interaction,
            pages: list[Production],
            client: TmdbClient,
            **kwargs,
    ):
        super().__init__(interaction, pages, **kwargs)
        self.client = client
        self.headline = None

    def embed(self) -> discord.Embed:
        selected = self.pages[self.page_index]
        if isinstance(selected, Movie):
            selected.genres = [self.client.movie_genres[genre_id] for genre_id in selected.genre_ids]
            embed = MovieView(self.latest_interaction, selected, self.client).embed()
            embed.remove_field(6).remove_field(5).remove_field(3).remove_field(1)
        elif isinstance(selected, Tv):
            selected.genres = [self.client.tv_genres[genre_id] for genre_id in selected.genre_ids]
            embed = TvView(self.latest_interaction, selected, self.client).embed()
            embed.remove_field(6).remove_field(4).remove_field(3).remove_field(1)
        else:
            raise RuntimeError('Object has to be an instance of Production.')
        if self.headline:
            embed.set_author(name=self.headline)
        embed.set_footer(text=f'Page {self.page_index + 1}/{self.page_count}')
        return embed

    @discord.ui.button(label='MORE', style=discord.ButtonStyle.blurple, row=1)
    async def more(self, interaction: discord.Interaction, button: discord.ui.Button):
        selected = self.pages[self.page_index]
        if isinstance(selected, Movie):
            production = await self.client.get_movie(selected.id)
            view = MovieView(interaction, production, self.client)
        elif isinstance(selected, Tv):
            production = await self.client.get_tv(selected.id)
            view = TvView(interaction, production, self.client)
        else:
            raise RuntimeError('Object has to be an instance of Production.')
        embed = view.embed()
        await interaction.response.edit_message(view=view, embed=embed)


class PersonPaginatingView(PaginatingView):
    def __init__(
            self,
            interaction: discord.Interaction,
            pages: list[Person],
            client: TmdbClient,
            **kwargs,
    ):
        super().__init__(interaction, pages, **kwargs)
        self.client = client

    def embed(self) -> discord.Embed:
        selected = self.pages[self.page_index]
        desc = f"**Known for: {selected.known_for_department if selected.known_for_department else '-'}**"
        known_for = '\n'.join(
            [f'[{p.title} ({p.release_date.year})]({p.web_url})' for p in selected.known_for])
        desc += '\n' + known_for
        embed = discord.Embed(
            title=selected.name,
            description=desc,
            url=selected.web_url,
            color=COLOR_EMBED_DARK
        )
        img_config = self.client.img_config
        if selected.profile_path:
            url = img_config.secure_base_url + img_config.profile_sizes[-1] + selected.profile_path
            embed.set_image(url=url)
        embed.set_footer(text=f'Page {self.page_index + 1}/{self.page_count}')
        return embed

    @discord.ui.button(label='MORE', style=discord.ButtonStyle.blurple, row=1)
    async def more(self, interaction: discord.Interaction, button: discord.ui.Button):
        selected = self.pages[self.page_index]
        person = await self.client.get_person(selected.id)
        view = PersonView(interaction, person, self.client)
        embed = view.embed()
        await interaction.response.edit_message(view=view, embed=embed)


class ProductionRecommendationView(ProductionPaginatingView):
    def __init__(
            self,
            interaction: discord.Interaction,
            pages: list[Production],
            client: TmdbClient,
            parent_view: ProductionView,
            **kwargs,
    ):
        super().__init__(interaction, pages, client, parent_view=parent_view, **kwargs)
        self.headline = f'Recommendations for {parent_view.production.title}'


class ProductionSimilarView(ProductionPaginatingView):
    def __init__(
            self,
            interaction: discord.Interaction,
            pages: list[Production],
            client: TmdbClient,
            parent_view: ProductionView,
            **kwargs,
    ):
        super().__init__(interaction, pages, client, parent_view=parent_view, **kwargs)
        self.headline = f'Similar to {parent_view.production.title}'
