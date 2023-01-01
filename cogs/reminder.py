import asyncio
import datetime as dt
import time
import zoneinfo
from typing import List

import asqlite
import discord
from discord import app_commands
from discord.ext import commands, tasks

from cogs.helper.reminder_helper import ReminderType, ReminderChannel
from config import database_path
from utils.misc import dm_open
from utils.constants import COLOR_EMBED_DARK
from utils.pagination import PageControlView, Paginator
from utils.misc import next_datetime, get_timezones


async def timezone_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    return [app_commands.Choice(name=tz, value=tz) for tz in get_timezones() if current.lower() in tz.lower()][:25]


class Reminder(commands.GroupCog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()
        self.check_reminders.start()

    def _update_reminder_check(self) -> None:
        if self.check_reminders.is_running():
            self.check_reminders.restart()
        else:
            self.check_reminders.start()

    def _display_list(self, paginator: Paginator) -> discord.Embed:
        page = paginator.page_content()
        embed = discord.Embed(
            title=f"Page {paginator.page + 1}/{paginator.last_page + 1}",
            color=COLOR_EMBED_DARK)
        for reminder in page:
            embed.add_field(
                name=f"{reminder['type']} ❰ {reminder['creation_timestamp']} ❱ <t:{reminder['reminder_timestamp']}>",
                value=reminder['description'],
                inline=False)
        return embed

    async def _reminder_add(self, interaction: discord.Interaction, reminder_type: ReminderType,
                            description: str,
                            location: ReminderChannel,
                            creation_timestamp: int,
                            reminder_timestamp: int):
        if reminder_timestamp <= creation_timestamp:
            await interaction.response.send_message('Error: Cannot set a reminder in the past.', ephemeral=True)
            return

        elif location == ReminderChannel.DM and not await dm_open(interaction.user):
            await interaction.response.send_message('Error: You do not accept Direct Messages.', ephemeral=True)
            return

        async with asqlite.connect(database_path) as db:
            user_id = interaction.user.id
            channel_id = interaction.channel_id if location == ReminderChannel.Here else None
            await db.execute("INSERT OR IGNORE INTO users (id) VALUES (?);", (user_id,))
            query = ("INSERT INTO reminders "
                     "(user_id, channel_id, type, creation_timestamp, reminder_timestamp, description) "
                     "VALUES (?, ?, ?, ?, ?, ?);")
            await db.execute(
                query, (user_id, channel_id, reminder_type.name, creation_timestamp, reminder_timestamp, description))
            await db.commit()

        await interaction.response.send_message(
            f"Reminder set!\n"
            f"Date: <t:{reminder_timestamp}:F> (<t:{reminder_timestamp}:R>)\n"
            f"Type: {reminder_type.name}\n"
            f"Location: **{location.name}**\n",
            ephemeral=True)

        self._update_reminder_check()

    @app_commands.command(name='list')
    async def reminder_list(self, interaction: discord.Interaction):
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

    @app_commands.command(name='delete')
    @app_commands.describe(timestamp='Creation ❰ timestamp ❱ of the reminder you wish to delete')
    async def reminder_delete(self, interaction: discord.Interaction, timestamp: int):
        """Deletes a set reminder"""
        async with asqlite.connect(database_path) as db:
            user_id = interaction.user.id
            await db.execute("INSERT OR IGNORE INTO users (id) VALUES (?);", (user_id,))
            query = f"DELETE FROM reminders WHERE user_id = ? AND creation_timestamp = ? RETURNING *;"
            deleted = await db.fetchone(query, (user_id, timestamp))
            await db.commit()

        if deleted:
            await interaction.response.send_message(f"Deleted ❰ {timestamp} ❱!", ephemeral=True)
            self._update_reminder_check()

        else:
            await interaction.response.send_message(f"Cannot delete: ❰ {timestamp} ❱ does not exist!", ephemeral=True)

    @app_commands.command()
    @app_commands.describe(description='Content of the reminder',
                           location='Where to send the reminder [default: Here]',
                           days='[default: 0]',
                           hours='[default: 0]',
                           minutes='[default: 0]')
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

        else:
            await self._reminder_add(
                interaction, ReminderType.Single, description, location, creation_timestamp, reminder_timestamp)

    @app_commands.command()
    @app_commands.autocomplete(timezone=timezone_autocomplete)
    @app_commands.describe(description='Content of the reminder',
                           when='YYYY/MM/DD hh:mm (24-hour clock)',
                           timezone='Timezone of the provided date and time',
                           location='Where to send the reminder [default: Here]')
    async def absolute(self, interaction: discord.Interaction,
                       description: str,
                       when: str,
                       timezone: str,
                       location: ReminderChannel = ReminderChannel.Here):
        """Sets a reminder scheduled for a chosen date"""
        creation_timestamp = int(time.time())

        try:
            datetime_object = dt.datetime.strptime(when, '%Y/%m/%d %H:%M').replace(tzinfo=zoneinfo.ZoneInfo(timezone))
        except ValueError:
            await interaction.response.send_message(
                'Error: Malformed date. Expected **YYYY/MM/DD hh:mm**', ephemeral=True)
            return
        except zoneinfo.ZoneInfoNotFoundError:
            await interaction.response.send_message(
                'Error: Malformed timezone', ephemeral=True)
            return

        reminder_timestamp = int(dt.datetime.timestamp(datetime_object))
        await self._reminder_add(
            interaction, ReminderType.Single, description, location, creation_timestamp, reminder_timestamp)

    @app_commands.command()
    @app_commands.autocomplete(timezone=timezone_autocomplete)
    @app_commands.describe(description='Content of the reminder',
                           when='Format: hh:mm (24-hour clock)',
                           timezone='Timezone of the provided date and time',
                           location='Where to send the reminder [default: Here]')
    async def daily(self, interaction: discord.Interaction,
                    description: str,
                    when: str,
                    timezone: str,
                    location: ReminderChannel = ReminderChannel.Here):
        """Sets a reminder scheduled to repeat each day"""
        creation_timestamp = int(time.time())

        try:
            datetime_object = dt.datetime.strptime(when, '%H:%M').replace(tzinfo=zoneinfo.ZoneInfo(timezone))
            datetime_object = next_datetime(dt.datetime.now(), datetime_object.hour, datetime_object.minute)
        except ValueError:
            await interaction.response.send_message(
                'Error: Malformed time. Expected **hh:mm**', ephemeral=True)
            return
        except zoneinfo.ZoneInfoNotFoundError:
            await interaction.response.send_message(
                'Error: Malformed timezone', ephemeral=True)
            return

        reminder_timestamp = int(dt.datetime.timestamp(datetime_object))
        await self._reminder_add(
            interaction, ReminderType.Daily, description, location, creation_timestamp, reminder_timestamp)

    @tasks.loop()
    async def check_reminders(self):
        async with asqlite.connect(database_path) as db:
            next_reminder = await db.fetchone("SELECT * FROM reminders ORDER BY reminder_timestamp ASC LIMIT 1")

        if next_reminder is None:
            self.check_reminders.cancel()
            return

        creation_timestamp = next_reminder['creation_timestamp']
        reminder_timestamp = next_reminder['reminder_timestamp']
        reminder_type = next_reminder['type']
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
            if reminder_type == ReminderType.Daily.name:
                reminder_timestamp += 86400
                query = "UPDATE reminders SET reminder_timestamp = ? WHERE user_id = ? AND creation_timestamp = ?;"
                await db.execute(query, (reminder_timestamp, user_id, creation_timestamp))
            else:
                query = "DELETE FROM reminders WHERE user_id = ? AND creation_timestamp = ?;"
                await db.execute(query, (user_id, creation_timestamp))
            await db.commit()


# -------------------------------------------------------------------------------------------------------------------- #
async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))
