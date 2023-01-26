import collections
from collections.abc import Callable

import discord

from utils.constants import EMBED_DESC_MAX_LENGTH, COLOR_EMBED_DARK
from utils.misc import trim_by_paragraph
from .helpers import verbose_date
from .models import Person, TmdbClient, Movie, Production, Tv
from ..shared_views import PaginatingView


class PersonView(discord.ui.View):
    """Primary view displayed when looking up a person."""

    def __init__(self, person: Person, client: TmdbClient):
        super().__init__()
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
            pages[department] = ['\n'.join(str(credit) for credit in dep_credits[x:x + credits_per_page]) for x in
                                 range(0, len(dep_credits), credits_per_page)]
        return pages

    def main_embed(self) -> discord.Embed:
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
        embed.add_field(name='Notable productions',
                        value=self.stringified_notable_credits if self.person.notable_credits else '-',
                        inline=False)
        embed.set_footer(
            text=f"Known for: {self.person.known_for_department if self.person.known_for_department else '-'}")
        return embed

    @discord.ui.button(label='FULL BIO', style=discord.ButtonStyle.gray, disabled=True)
    async def biography(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays full biography when pressed."""
        pages = self._paginate_bio()
        view = PersonBiographySubview(self, pages)
        embed = view.biography_embed()
        await interaction.response.edit_message(view=view, embed=embed)

    @discord.ui.button(label='GALLERY', style=discord.ButtonStyle.gray, disabled=True)
    async def images(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays image gallery when pressed."""
        img_config = self.client.img_config
        pages = [
            img_config.secure_base_url + img_config.profile_sizes[-1] + img.file_path for img in self.person.images]
        view = PersonImageSubview(self, pages)
        embed = view.images_embed()
        await interaction.response.edit_message(view=view, embed=embed)

    @discord.ui.button(label='CREDITS', style=discord.ButtonStyle.gray, disabled=True)
    async def credits(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays complete credits when pressed."""
        pages = self._paginate_credits()
        view = PersonCreditsSubview(self, pages)
        embed = view.credits_embed()
        await interaction.response.edit_message(view=view, embed=embed)


class ProductionView(discord.ui.View):
    def __init__(self, production: Production, client: TmdbClient):
        super().__init__()
        self.production = production
        self.client = client
        if self.production.credits:
            self.credits.disabled = False

    def _paginate_credits(self, credits_per_page: int = 20) -> dict[str, list[str]]:
        """Turns credits into strings for display and splits them into lists of pages for every category."""
        pages = collections.defaultdict(list)
        for credit in sorted(self.production.credits):
            pages[credit.department].append(credit)
        for department, dep_credits in pages.items():
            pages[department] = ['\n'.join(str(credit) for credit in dep_credits[x:x + credits_per_page]) for x in
                                 range(0, len(dep_credits), credits_per_page)]
        return pages

    def _embed_description(self):
        if self.production.tagline:
            return f'**{self.production.tagline}**\n\n{self.production.overview}'
        else:
            return self.production.overview

    def _embed_title(self):
        if self.production.release_date:
            return f'{self.production.title} ({self.production.release_date.year})'
        else:
            return self.production.title

    def _base_embed(self) -> discord.Embed:
        embed = discord.Embed(title=self._embed_title(),
                              description=self._embed_description(),
                              url=self.production.web_url,
                              color=COLOR_EMBED_DARK)
        img_config = self.client.img_config
        if self.production.poster_path:
            url = img_config.secure_base_url + img_config.poster_sizes[-1] + self.production.poster_path
            embed.set_thumbnail(url=url)
        if self.production.backdrop_path:
            url = img_config.secure_base_url + img_config.backdrop_sizes[-1] + self.production.backdrop_path
            embed.set_image(url=url)
        embed.add_field(name='Genres',
                        value=', '.join(self.production.genres) if self.production.genres else '-',
                        inline=False)
        embed.add_field(name='Status', value=self.production.status if self.production.status else '-')
        embed.add_field(name='User score', value=self.production.pretty_score())
        embed.set_footer(text=', '.join(self.production.keywords))
        return embed

    @discord.ui.button(label='CREDITS', style=discord.ButtonStyle.gray, disabled=True)
    async def credits(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays complete credits when pressed."""
        pages = self._paginate_credits()
        view = ProductionCreditsSubview(self, pages)
        embed = view.credits_embed()
        await interaction.response.edit_message(view=view, embed=embed)


class MovieView(ProductionView):
    def __init__(self, movie: Movie, client: TmdbClient):
        super().__init__(movie, client)
        self.movie = movie

    def main_embed(self) -> discord.Embed:
        """Returns the embed used for displaying the movie's primary information."""
        embed = self._base_embed()
        embed.add_field(name='Runtime', value=self.movie.pretty_runtime())
        embed.add_field(name='Release date',
                        value=verbose_date(self.movie.release_date) if self.movie.release_date else '-')
        embed.add_field(name='Budget', value=f'${self.movie.budget:,}' if self.movie.budget else '-')
        embed.add_field(name='Revenue', value=f'${self.movie.revenue:,}' if self.movie.revenue else '-')
        if directors := [credit.credit_subject for credit in self.movie.credits if 'Director' in credit.jobs]:
            embed.set_author(name='Directed by ' + ', '.join([director for director in directors]))
        return embed


class TvView(ProductionView):
    def __init__(self, tv: Tv, client: TmdbClient):
        super().__init__(tv, client)
        self.tv = tv

    def main_embed(self) -> discord.Embed:
        """Returns the embed used for displaying the movie's primary information."""
        embed = self._base_embed()
        embed.add_field(name='Episode runtime', value=self.tv.pretty_runtime())
        embed.add_field(name='Type', value=self.tv.type)
        embed.add_field(name='First aired', value=verbose_date(self.tv.release_date) if self.tv.release_date else '-')
        embed.add_field(name='Last aired', value=verbose_date(self.tv.last_air_date) if self.tv.last_air_date else '-')
        if self.tv.created_by:
            embed.set_author(name='Created by ' + ', '.join([person.name for person in self.tv.created_by]))
        return embed


class PaginatingSubview(PaginatingView):
    """View that expands PaginatingView with a button returning the user to the previous view."""

    def __init__(self, parent_view: PersonView | ProductionView, pages: list | dict[str, list],
                 embed_constructor: Callable[..., discord.Embed]):
        super().__init__(pages, embed_constructor)
        self.parent_view = parent_view
        # We rearrange view.children to put the return button on the left.
        children = self.children
        idx, return_button = discord.utils.find(lambda x: x[1].style == discord.ButtonStyle.red, enumerate(children))
        children.pop(idx)
        self.clear_items()
        for child in [return_button] + children:
            self.add_item(child)

    @discord.ui.button(label='RETURN', style=discord.ButtonStyle.red, row=1)
    async def return_to_main_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that returns user to the person's main page."""
        await interaction.response.edit_message(view=self.parent_view, embed=self.parent_view.main_embed())


class PersonBiographySubview(PaginatingSubview):
    """Subview that displays the person's full biography."""

    def __init__(self, parent_view: PersonView, pages: list | dict[str, list]):
        super().__init__(parent_view, pages, self.biography_embed)

    def biography_embed(self, **kwargs) -> discord.Embed:
        """Creates the biography display embed."""
        index: int = kwargs.get('index', 0)
        embed = discord.Embed(title=self.parent_view.person.name,
                              description=self.pages[index],
                              url=self.parent_view.person.web_url,
                              color=COLOR_EMBED_DARK)
        embed.set_author(name='FULL BIO')
        embed.set_footer(text=f'Page {index + 1}/{self.page_count}')
        return embed


class PersonImageSubview(PaginatingSubview):
    """Subview that displays the person's image gallery."""

    def __init__(self, parent_view: PersonView, pages: list | dict[str, list]):
        super().__init__(parent_view, pages, self.images_embed)

    def images_embed(self, **kwargs) -> discord.Embed:
        """Creates the image display embed."""
        index: int = kwargs.get('index', 0)
        embed = discord.Embed(title=self.parent_view.person.name,
                              url=self.parent_view.person.web_url,
                              color=COLOR_EMBED_DARK)
        embed.set_image(url=self.pages[index])
        embed.set_author(name='PICTURES')
        embed.set_footer(text=f'Picture {index + 1}/{self.page_count}')
        return embed


class CreditsSubview(PaginatingSubview):
    def __init__(self, parent_view: PersonView | ProductionView, pages: list | dict[str, list]):
        super().__init__(parent_view, pages, self.credits_embed)

    def credits_embed(self, **kwargs) -> discord.Embed:
        raise NotImplementedError

    @discord.ui.select(row=0)
    async def department(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Menu that allows the user to choose the credits department."""
        self.constructor_kwargs['category'] = select.values[0]
        self.constructor_kwargs['index'] = 0
        self.page_count = len(self.pages[self.constructor_kwargs['category']])
        self.previous_page.disabled = True
        if self.page_count == 1:
            self.next_page.disabled = True
        else:
            self.next_page.disabled = False
        for opt in select.options:
            opt.default = False
        selected_option = discord.utils.get(select.options, value=select.values[0])
        selected_option.default = True
        return await interaction.response.edit_message(embed=self.embed_constructor(**self.constructor_kwargs),
                                                       view=self)


class PersonCreditsSubview(CreditsSubview):
    """Subview that displays the person's credits."""

    def __init__(self, parent_view: PersonView, pages: list | dict[str, list]):
        super().__init__(parent_view, pages)
        self.page_count = len(self.pages[self.parent_view.person.known_for_department])
        for department in self.pages.keys():
            if department == self.parent_view.person.known_for_department:
                self.department.append_option(discord.SelectOption(label=department, default=True))
            else:
                self.department.append_option(discord.SelectOption(label=department))
        if self.page_count == 1:
            self.next_page.disabled = True
        else:
            self.next_page.disabled = False

    def credits_embed(self, **kwargs) -> discord.Embed:
        """Creates the credits display embed."""
        category: str = kwargs.get('category', self.parent_view.person.known_for_department)
        index: int = kwargs.get('index', 0)
        embed = discord.Embed(title=self.parent_view.person.name,
                              description=self.pages[category][index],
                              url=self.parent_view.person.web_url,
                              color=COLOR_EMBED_DARK)
        embed.set_author(name='CREDITS')
        embed.set_footer(text=f'Page {index + 1}/{self.page_count}')
        return embed


class ProductionCreditsSubview(CreditsSubview):
    """Subview that displays the production's credits."""

    def __init__(self, parent_view: ProductionView, pages: list | dict[str, list]):
        super().__init__(parent_view, pages)
        self.main_page = 'Acting'
        self.page_count = len(self.pages[self.main_page])
        if self.page_count == 0:
            self.pages.pop('Acting')
            self.main_page = sorted(self.pages, key=lambda x: len(self.pages[x]))[0]
            self.page_count = len(self.pages[self.main_page])
        for department in self.pages.keys():
            if department == self.main_page:
                self.department.append_option(discord.SelectOption(label=department, default=True))
            else:
                self.department.append_option(discord.SelectOption(label=department))
        if self.page_count == 1:
            self.next_page.disabled = True
        else:
            self.next_page.disabled = False

    def credits_embed(self, **kwargs) -> discord.Embed:
        """Creates the credits display embed."""
        category: str = kwargs.get('category', self.main_page)
        index: int = kwargs.get('index', 0)
        embed = discord.Embed(title=self.parent_view.production.title,
                              description=self.pages[category][index],
                              url=self.parent_view.production.web_url,
                              color=COLOR_EMBED_DARK)
        embed.set_author(name='CREDITS')
        embed.set_footer(text=f'Page {index + 1}/{self.page_count}')
        return embed
