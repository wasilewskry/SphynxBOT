import asyncio
import time

import asqlite
import discord
from discord import app_commands
from discord.ext import commands, tasks

from config import database_path
from utils.direct_messages import dm_open
from utils.pagination import PageControlView, Paginator
from utils.reminder_definitions import ReminderChannel, COLOR_EMBED_DARK


class Reminder(commands.GroupCog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()
        self.check_regular_reminders.start()

    def _display_list(self, paginator: Paginator) -> discord.Embed:
        page = paginator.page_content()
        embed = discord.Embed(
            title=f"Page {paginator.page+1}/{paginator.last_page+1}",
            color=COLOR_EMBED_DARK)
        for reminder in page:
            embed.add_field(
                name=f"❰ {reminder['creation_timestamp']} ❱ <t:{reminder['reminder_timestamp']}>",
                value=reminder['description'],
                inline=False)
        return embed

    @app_commands.command(name='list')
    async def regular_list(self, interaction: discord.Interaction):
        """Lists currently set reminders"""
        async with asqlite.connect(database_path) as db:
            reminders = await db.fetchall(
                f"SELECT * FROM reminders "
                f"WHERE user_id = {interaction.user.id} "
                f"ORDER BY reminder_timestamp")

        if not reminders:
            await interaction.response.send_message("No reminders set right now.", ephemeral=True)
        else:
            paginator = Paginator(reminders)
            view = PageControlView(paginator, self._display_list)
            await interaction.response.send_message(embed=self._display_list(paginator), view=view, ephemeral=True)

    relative = app_commands.Group(name='relative', description='Reminders set in relation to time of execution')

    @relative.command(name='add')
    @app_commands.describe(description='Content of the reminder',
                           location='Where to send the reminder [default: Here]',
                           days='[default: 0]',
                           hours='[default: 0]',
                           minutes='[default: 0]')
    async def relative_add(self, interaction: discord.Interaction,
                           description: str,
                           location: ReminderChannel = ReminderChannel.Here,
                           days: int = 0,
                           hours: int = 0,
                           minutes: int = 0):
        """Sets a reminder scheduled in relation to present moment"""
        creation_timestamp = int(time.time())
        timedelta = 86400 * days + 3600 * hours + 60 * minutes
        reminder_timestamp = creation_timestamp + timedelta

        if timedelta <= 0:
            await interaction.response.send_message('Error: Time not specified or negative.', ephemeral=True)
            return

        if location == ReminderChannel.DM and not await dm_open(interaction.user):
            await interaction.response.send_message('Error: You do not accept Direct Messages.', ephemeral=True)
            return

        async with asqlite.connect(database_path) as db:
            user_id = interaction.user.id
            channel_id = interaction.channel_id if location == ReminderChannel.Here else None
            await db.execute("INSERT OR IGNORE INTO users (id) VALUES (?);", (user_id,))
            query = ("INSERT INTO reminders (user_id, channel_id, creation_timestamp, reminder_timestamp, description) "
                     "VALUES (?, ?, ?, ?, ?);")
            await db.execute(query, (user_id, channel_id, creation_timestamp, reminder_timestamp, description))
            await db.commit()

        await interaction.response.send_message(
            f"Reminder set!\n"
            f"Date: <t:{reminder_timestamp}:F> (<t:{reminder_timestamp}:R>)\n"
            f"Location: **{location.name}**",
            ephemeral=True)

        if self.check_regular_reminders.is_running():
            self.check_regular_reminders.restart()
        else:
            self.check_regular_reminders.start()

    @tasks.loop()
    async def check_regular_reminders(self):
        async with asqlite.connect(database_path) as db:
            next_reminder = await db.fetchone("SELECT * FROM reminders ORDER BY reminder_timestamp ASC LIMIT 1")

        if next_reminder is None:
            self.check_regular_reminders.cancel()
            return

        creation_timestamp = next_reminder['creation_timestamp']
        reminder_timestamp = next_reminder['reminder_timestamp']
        user_id = next_reminder['user_id']
        channel_id = next_reminder['channel_id']
        description = next_reminder['description']

        await asyncio.sleep(reminder_timestamp - int(time.time()))

        reminder = f"<@{user_id}>\n{description}"
        if channel_id:
            channel = await self.bot.fetch_channel(channel_id)
            await channel.send(reminder)
        else:
            user = await self.bot.fetch_user(user_id)
            if await dm_open(user):
                await user.send(reminder)

        async with asqlite.connect(database_path) as db:
            query = "DELETE FROM reminders WHERE user_id = ? AND creation_timestamp = ?;"
            await db.execute(query, (user_id, creation_timestamp))
            await db.commit()


# -------------------------------------------------------------------------------------------------------------------- #
async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))
