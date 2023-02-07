import discord

from cogs.shared_views import PaginatingView
from utils.constants import COLOR_EMBED_DARK
from .models import Reminder


class ReminderView(PaginatingView):
    def __init__(self, pages: list[Reminder]):
        super().__init__(pages, self.embed)

    def embed(self, **kwargs) -> discord.Embed:
        index: int = kwargs.get('index', 0)
        reminder = self.pages[index]
        epoch = int(reminder.target_time.timestamp())
        embed = discord.Embed(
            title=f"<t:{epoch}>",
            description=reminder.description,
            color=COLOR_EMBED_DARK)
        embed.set_author(name=f'Reminder id: {reminder.id}\nReminder type: {reminder.reminder_type.name}')
        embed.set_footer(text=f'Reminder {index + 1}/{len(self.pages)}')
        return embed
