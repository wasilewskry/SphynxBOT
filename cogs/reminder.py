import asyncio
import time

import asqlite
import discord
from discord import app_commands
from discord.ext import commands, tasks

from config import database_path
from utils.direct_messages import dm_open
from utils.reminder_definitions import ReminderChannel


class Reminder(commands.GroupCog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()
        self.check_reminders.start()

    @app_commands.command()
    @app_commands.describe(description='Content of the reminder',
                           location='Where to send the reminder [default: Here]',
                           days='How many days from now [default: 0]',
                           hours='How many hours from now [default: 0]',
                           minutes='How many minutes from now [default: 0]')
    async def relative(self, interaction: discord.Interaction,
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
            f"Reminder will be posted in {location.name}, {days} days {hours} hours {minutes} minutes from now.",
            ephemeral=True)

        if self.check_reminders.is_running():
            self.check_reminders.restart()
        else:
            self.check_reminders.start()

    @tasks.loop()
    async def check_reminders(self):
        async with asqlite.connect(database_path) as db:
            next_reminder = await db.fetchone("SELECT * FROM reminders ORDER BY reminder_timestamp ASC LIMIT 1")
            if next_reminder is None:
                self.check_reminders.cancel()

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

            query = "DELETE FROM reminders WHERE user_id = ? AND creation_timestamp = ?;"
            await db.execute(query, (user_id, creation_timestamp))
            await db.commit()


# -------------------------------------------------------------------------------------------------------------------- #
async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))
