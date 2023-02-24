import discord


class SphynxView(discord.ui.View):
    """Base view that all other views used by the bot should inherit from."""

    def __init__(self, interaction: discord.Interaction, *, author: discord.User = None, timeout: int = 120, **kwargs):
        super().__init__(timeout=timeout)
        self.latest_interaction = interaction
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction):
        if not self.author or interaction.user == self.author:
            self.latest_interaction = interaction
            return True
        else:
            return False

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.latest_interaction.edit_original_response(view=self)

    def embed(self) -> discord.Embed:
        raise NotImplementedError()


class PaginatingView(SphynxView):
    def __init__(
            self,
            interaction: discord.Interaction,
            pages: list | dict[str, list],
            *,
            parent_view: SphynxView = None,
            **kwargs
    ):
        super().__init__(interaction, **kwargs)
        self.pages = pages
        self.page_count = len(self.pages)
        self.page_index = 0
        if self.page_count > 1:
            self.next_page.disabled = False
        self.parent_view = parent_view
        if not self.parent_view:
            # Discord does not allow to explicitly set position of they button
            # New buttons appear in order of creation from left to right
            # In order to keep the return button on the left, we create it first and then remove it if it's unnecessary
            children = self.children
            idx, return_button = discord.utils.find(
                lambda x: x[1].label == 'RETURN', enumerate(children))
            children.pop(idx)
            self.clear_items()
            for child in children:
                self.add_item(child)

    @discord.ui.button(label='RETURN', style=discord.ButtonStyle.red, row=1)
    async def return_to_main_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays the parent view again."""
        await interaction.response.edit_message(view=self.parent_view, embed=self.parent_view.embed())

    @discord.ui.button(label='PREV', style=discord.ButtonStyle.gray, row=1, disabled=True)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays the previous page."""
        self.page_index -= 1
        self.next_page.disabled = False
        if self.page_index == 0:
            button.disabled = True
        await interaction.response.edit_message(view=self, embed=self.embed())

    @discord.ui.button(label='NEXT', style=discord.ButtonStyle.gray, row=1, disabled=True)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button that displays the next page."""
        self.page_index += 1
        self.previous_page.disabled = False
        if self.page_index == self.page_count - 1:
            button.disabled = True
        await interaction.response.edit_message(view=self, embed=self.embed())
