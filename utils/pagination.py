import discord
import typing


class Paginator:
    def __init__(self, content: list, page_size: int = 5):
        self.content = content
        self.page_size = page_size
        self.last_page = len(content) // (page_size + 1)
        self.page = 0

    def page_content(self):
        return self.content[self.page*self.page_size:(self.page+1)*self.page_size]

    def first(self):
        self.page = 0
        return self.page_content()

    def last(self):
        self.page = self.last_page
        return self.page_content()

    def next(self):
        if self.page != self.last_page:
            self.page += 1
        return self.page_content()

    def previous(self):
        if self.page != 0:
            self.page -= 1
        return self.page_content()


class PageControlView(discord.ui.View):
    def __init__(self, paginator: Paginator, display_func: typing.Callable[[Paginator], discord.Embed]):
        super().__init__()
        self.paginator = paginator
        self.display_func = display_func
        if self.paginator.last_page == 0:
            self.next.disabled = True
            self.last.disabled = True

    @discord.ui.button(label='First', style=discord.ButtonStyle.gray, disabled=True)
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.paginator.first()
        self.previous.disabled = True
        self.first.disabled = True
        self.next.disabled = False
        self.last.disabled = False

        await interaction.response.edit_message(embed=self.display_func(self.paginator), view=self)

    @discord.ui.button(label='Previous', style=discord.ButtonStyle.gray, disabled=True)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.paginator.previous()
        if self.paginator.page == 0:
            self.previous.disabled = True
            self.first.disabled = True
        self.next.disabled = False
        self.last.disabled = False

        await interaction.response.edit_message(embed=self.display_func(self.paginator), view=self)

    @discord.ui.button(label='Next', style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.paginator.next()
        if self.paginator.page == self.paginator.last_page:
            self.next.disabled = True
            self.last.disabled = True
        self.previous.disabled = False
        self.first.disabled = False

        await interaction.response.edit_message(embed=self.display_func(self.paginator), view=self)

    @discord.ui.button(label='Last', style=discord.ButtonStyle.gray)
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.paginator.last()
        self.next.disabled = True
        self.last.disabled = True
        self.previous.disabled = False
        self.first.disabled = False

        await interaction.response.edit_message(embed=self.display_func(self.paginator), view=self)
