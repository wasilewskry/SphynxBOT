from collections.abc import Callable

import discord


class PaginatingView(discord.ui.View):
    """Simple pagination view with buttons to show next or previous page."""

    def __init__(self, pages: list | dict[str, list], embed_constructor: Callable[..., discord.Embed]):
        super().__init__()
        self.pages = pages
        self.page_count = len(pages)
        self.embed_constructor = embed_constructor
        self.constructor_kwargs = {'index': 0}
        if self.page_count > 1:
            self.next_page.disabled = False

    @discord.ui.button(label='PREV', style=discord.ButtonStyle.gray, row=1, disabled=True)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays the previous page."""
        self.constructor_kwargs['index'] -= 1
        self.next_page.disabled = False
        if self.constructor_kwargs['index'] == 0:
            button.disabled = True
        await interaction.response.edit_message(view=self, embed=self.embed_constructor(**self.constructor_kwargs))

    @discord.ui.button(label='NEXT', style=discord.ButtonStyle.gray, row=1, disabled=True)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays the next page."""
        self.constructor_kwargs['index'] += 1
        self.previous_page.disabled = False
        if self.constructor_kwargs['index'] == self.page_count - 1:
            button.disabled = True
        await interaction.response.edit_message(view=self, embed=self.embed_constructor(**self.constructor_kwargs))
