import discord

from cogs.shared_views import PaginatingView
from utils.constants import COLOR_EMBED_DARK
from .models import Reminder


class ReminderView(PaginatingView):
    def __init__(
            self,
            interaction: discord.Interaction,
            reminders: list[Reminder],
            **kwargs,
    ):
        super().__init__(interaction, reminders, **kwargs)

    def embed(self) -> discord.Embed:
        reminder = self.pages[self.page_index]
        epoch = int(reminder.target_time.timestamp())
        embed = discord.Embed(
            title=f"<t:{epoch}>",
            description=reminder.description,
            color=COLOR_EMBED_DARK)
        embed.set_author(name=f'Reminder id: {reminder.id}\nReminder type: {reminder.reminder_type.name}')
        embed.set_footer(text=f'Reminder {self.page_index + 1}/{len(self.pages)}')
        return embed
