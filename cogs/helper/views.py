import collections
from typing import List, Dict, Any, Callable

import discord

from cogs.helper.cinema_helper import Person, TMDB_IMAGE_BASE_URL, TMDB_PROFILE_SIZES, TMDB_WEB_BASE_URL
from utils.constants import COLOR_EMBED_DARK


class PaginatingView(discord.ui.View):
    def __init__(self, embed_constructor: Callable[..., discord.Embed] = None, pages: List = None):
        super().__init__()
        self.pages = pages
        self.page_count = len(self.pages) if self.pages else 0
        self.embed_constructor = embed_constructor
        self.constructor_kwargs = {'index': 0, 'pages': self.pages}
        if self.page_count > 1:
            self.next_page.disabled = False

    @discord.ui.button(label='PREV', style=discord.ButtonStyle.gray, row=1, disabled=True)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays the previous page."""
        self.constructor_kwargs['index'] -= 1
        self.next_page.disabled = False
        if self.constructor_kwargs['index'] == 0:
            button.disabled = True
        await interaction.response.edit_message(embed=self.embed_constructor(**self.constructor_kwargs), view=self)

    @discord.ui.button(label='NEXT', style=discord.ButtonStyle.gray, row=1, disabled=True)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays the next page."""
        self.constructor_kwargs['index'] += 1
        self.previous_page.disabled = False
        if self.constructor_kwargs['index'] == self.page_count - 1:
            button.disabled = True
        await interaction.response.edit_message(embed=self.embed_constructor(**self.constructor_kwargs), view=self)


class CinemaPersonView(discord.ui.View):
    def __init__(self, person: Person):
        super().__init__()
        self.person = person
        self.image_urls = [TMDB_IMAGE_BASE_URL + TMDB_PROFILE_SIZES[-1] + img_path for img_path in self.person.images]
        self.image_count = len(self.image_urls)
        self.paginated_bio = self._paginate_bio()
        self.bio_page_count = len(self.paginated_bio)
        self.paginated_credits = self._paginate_credits()
        self.credits_page_counts = {key: len(value) for key, value in self.paginated_credits.items()}

        if self.image_count:
            self.pictures.disabled = False

        if self.person.biography != self.person.short_bio:
            self.full_bio.disabled = False

        if self.paginated_credits:
            self.personal_credits.disabled = False

    def _paginate_bio(self, page_size: int = 1500) -> List[str]:
        """Splits biography into pages."""
        sentences = self.person.biography.split('.')
        pages = []
        p = ''
        if sentences[-1] == '':
            sentences = sentences[:-1]
        for sent in sentences:
            if len(p) + len(sent) + 1 < page_size:
                p += sent + '.'
            else:
                pages.append(p)
                p = sent + '.'
        pages.append(p)
        return pages

    def _categorize_credits(self) -> Dict[str, List[Dict[str, Any]]]:
        """Divides credits into categories."""
        categorized = collections.defaultdict(list)
        if self.person.credits_cast:
            categorized['Acting'] = self.person.credits_cast
        for c in self.person.credits_crew:
            categorized[c['department']].append(c)
        for cat in categorized:
            categorized[cat] = sorted(categorized[cat], key=lambda x: x['release_date'].split('-'), reverse=True)
        return categorized

    def _paginate_credits(self, page_size: int = 20) -> Dict[str, List[str]]:
        """Turns credits into strings for display and splits them into lists of pages for every category."""
        paginated = {}
        categorized = self._categorize_credits()
        for cat, creds in categorized.items():
            with_year = []
            without_year = []
            for c in creds:
                year = c['release_date'].partition('-')[0] if c['release_date'] else '----'
                url = f"{TMDB_WEB_BASE_URL}/{c['media_type']}/{c['id']}"
                line = f"``{year}`` ⬤ [{c['title']}]({url})"
                if cat == 'Acting':
                    line += f" as {c['character']}"
                else:
                    line += f" ... {c['job']}"
                if c['release_date']:
                    with_year.append(line)
                else:
                    without_year.append(line)
            processed = without_year + with_year
            paginated[cat] = ['\n'.join(processed[x:x + page_size]) for x in range(0, len(processed), page_size)]
        return paginated

    def image_embed(self, index: int = 0, **kwargs) -> discord.Embed:
        """Creates the image display embed."""
        embed = discord.Embed(title=self.person.name, url=self.person.profile_url, color=COLOR_EMBED_DARK)
        embed.set_image(url=self.image_urls[index])
        embed.set_author(name='PICTURES')
        embed.set_footer(text=f'Picture {index + 1}/{self.image_count}')
        return embed

    def bio_embed(self, index: int = 0, **kwargs) -> discord.Embed:
        """Creates the biography display embed."""
        embed = discord.Embed(title=self.person.name,
                              description=self.paginated_bio[index],
                              url=self.person.profile_url,
                              color=COLOR_EMBED_DARK)
        embed.set_author(name='FULL BIO')
        embed.set_footer(text=f'Page {index + 1}/{self.bio_page_count}')
        return embed

    def credits_embed(self, category: str, index: int = 0, **kwargs) -> discord.Embed:
        """Creates the credits display embed."""
        embed = discord.Embed(title=self.person.name,
                              description=self.paginated_credits[category][index],
                              url=self.person.profile_url,
                              color=COLOR_EMBED_DARK)
        embed.set_author(name='CREDITS')
        embed.set_footer(text=f'Page {index + 1}/{self.credits_page_counts[category]}')
        return embed

    @discord.ui.button(label='FULL BIO', style=discord.ButtonStyle.gray, disabled=True)
    async def full_bio(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays full biography when pressed."""
        embed = self.bio_embed()
        view = CinemaPersonBioView(self)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label='PICTURES', style=discord.ButtonStyle.gray, disabled=True)
    async def pictures(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays image gallery when pressed."""
        embed = self.image_embed()
        view = CinemaPersonPictureView(self)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label='CREDITS', style=discord.ButtonStyle.gray, disabled=True)
    async def personal_credits(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays complete credits when pressed."""
        embed = self.credits_embed(self.person.known_for_department)
        view = CinemaPersonCreditsView(self)
        await interaction.response.edit_message(embed=embed, view=view)


class CinemaPersonBaseSubview(PaginatingView):
    def __init__(self, parent_view: CinemaPersonView, **kwargs):
        super().__init__(**kwargs)
        self.parent_view = parent_view

    @discord.ui.button(label='RETURN', style=discord.ButtonStyle.red, row=1)
    async def return_to_main_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays the main embed."""
        await interaction.response.edit_message(embed=self.parent_view.person.main_embed(), view=self.parent_view)


class CinemaPersonBioView(CinemaPersonBaseSubview):
    def __init__(self, parent_view: CinemaPersonView, **kwargs):
        super().__init__(parent_view, **kwargs)
        self.page_count = self.parent_view.bio_page_count
        self.embed_constructor = self.parent_view.bio_embed
        if self.page_count > 1:
            self.next_page.disabled = False


class CinemaPersonPictureView(CinemaPersonBaseSubview):
    def __init__(self, parent_view: CinemaPersonView, **kwargs):
        super().__init__(parent_view, **kwargs)
        self.page_count = self.parent_view.image_count
        self.embed_constructor = self.parent_view.image_embed
        if self.page_count > 1:
            self.next_page.disabled = False


class CinemaPersonCreditsView(CinemaPersonBaseSubview):
    def __init__(self, parent_view: CinemaPersonView, **kwargs):
        super().__init__(parent_view, **kwargs)
        self.constructor_kwargs['category'] = self.parent_view.person.known_for_department
        self.page_count = self.parent_view.credits_page_counts[self.constructor_kwargs['category']]
        self.embed_constructor = self.parent_view.credits_embed
        for dep in self.parent_view.paginated_credits.keys():
            if dep == self.parent_view.person.known_for_department:
                self.department.append_option(discord.SelectOption(label=dep, default=True))
            else:
                self.department.append_option(discord.SelectOption(label=dep))
        if self.page_count > 1:
            self.next_page.disabled = False

    @discord.ui.select(row=0)
    async def department(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Menu that allows the user to choose the credits department."""
        self.constructor_kwargs['category'] = select.values[0]
        self.constructor_kwargs['index'] = 0
        self.page_count = self.parent_view.credits_page_counts[self.constructor_kwargs['category']]
        self.previous_page.disabled = True
        if self.parent_view.credits_page_counts[self.constructor_kwargs['category']] == 1:
            self.next_page.disabled = True
        else:
            self.next_page.disabled = False
        for opt in select.options:
            opt.default = False
        selected_option = discord.utils.get(select.options, value=select.values[0])
        selected_option.default = True
        return await interaction.response.edit_message(embed=self.embed_constructor(**self.constructor_kwargs),
                                                       view=self)
