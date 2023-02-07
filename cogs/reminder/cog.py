import datetime as dt
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord import app_commands
from discord.ext import commands, tasks

from cogs.shared_models import User
from run import Sphynx
from utils.misc import dm_open, get_timezones, next_datetime
from .helpers import ReminderChannel, ReminderType
from .models import Reminder
from .views import ReminderView


async def timezone_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    return [app_commands.Choice(name=tz, value=tz) for tz in get_timezones() if current.lower() in tz.lower()][:25]


class ReminderCog(commands.GroupCog, group_name='reminder'):
    def __init__(self, bot: Sphynx):
        self.bot = bot
        self.check_reminders.start()

    def _update_reminder_check(self) -> None:
        if self.check_reminders.is_running():
            self.check_reminders.restart()
        else:
            self.check_reminders.start()

    async def _reminder_add(
            self,
            interaction: discord.Interaction,
            reminder_type: ReminderType,
            description: str,
            location: ReminderChannel,
            target_time: dt.datetime
    ):
        """Adds a new reminder."""
        time_now = discord.utils.utcnow()
        if len(description) > 2048:
            await interaction.response.send_message('Error: Description too long. Max length is 2048.', ephemeral=True)
            return
        if (target_time - time_now).total_seconds() < 60:
            await interaction.response.send_message(
                'Error: Reminder should be set no less than a minute from now.', ephemeral=True)
            return
        if location == ReminderChannel.dm and not await dm_open(interaction.user):
            await interaction.response.send_message('Error: You do not accept direct messages.', ephemeral=True)
            return
        guild_id = interaction.guild_id if location == ReminderChannel.here else None
        channel_id = interaction.channel_id if location == ReminderChannel.here else None
        user, _ = await User.get_or_create(id=interaction.user.id)
        await Reminder.create(
            user=user,
            guild_id=guild_id,
            channel_id=channel_id,
            reminder_type=reminder_type,
            target_time=target_time,
            description=description
        )
        epoch = int(target_time.timestamp())
        await interaction.response.send_message(
            f"Reminder set!\n"
            f"Date: <t:{epoch}:F> (<t:{epoch}:R>)\n"
            f"Type: {reminder_type.name}\n"
            f"Location: **{location.name}**\n",
            ephemeral=True
        )
        self._update_reminder_check()

    @app_commands.command()
    @app_commands.describe(
        description='Content of the reminder',
        location='Where to send the reminder [default: here]',
        days='[default: 0]',
        hours='[default: 0]',
        minutes='[default: 0]'
    )
    async def relative(
            self,
            interaction: discord.Interaction,
            description: str,
            location: ReminderChannel = ReminderChannel.here,
            days: int = 0,
            hours: int = 0,
            minutes: int = 0
    ):
        """Sets a reminder scheduled in relation to present moment."""
        target_time = discord.utils.utcnow() + dt.timedelta(days=days, hours=hours, minutes=minutes)
        await self._reminder_add(interaction, ReminderType.single, description, location, target_time)

    @app_commands.command()
    @app_commands.autocomplete(timezone=timezone_autocomplete)
    @app_commands.describe(
        description='Content of the reminder',
        when='YYYY/MM/DD hh:mm (24-hour clock)',
        timezone='Timezone of the provided date and time',
        location='Where to send the reminder [default: here]'
    )
    async def absolute(
            self,
            interaction: discord.Interaction,
            description: str,
            when: str,
            timezone: str,
            location: ReminderChannel = ReminderChannel.here
    ):
        """Sets a reminder scheduled for a chosen date."""
        try:
            target_time = dt.datetime.strptime(when, '%Y/%m/%d %H:%M').replace(tzinfo=ZoneInfo(timezone))
        except ValueError:
            await interaction.response.send_message('Error: Malformed date.', ephemeral=True)
        except ZoneInfoNotFoundError:
            await interaction.response.send_message('Error: Malformed timezone.', ephemeral=True)
        else:
            await self._reminder_add(interaction, ReminderType.single, description, location, target_time)

    @app_commands.command()
    @app_commands.autocomplete(timezone=timezone_autocomplete)
    @app_commands.describe(
        description='Content of the reminder',
        when='Format: hh:mm (24-hour clock)',
        timezone='Timezone of the provided date and time',
        location='Where to send the reminder [default: here]'
    )
    async def daily(
            self,
            interaction: discord.Interaction,
            description: str,
            when: str,
            timezone: str,
            location: ReminderChannel = ReminderChannel.here
    ):
        """Sets a reminder scheduled to repeat each day."""
        try:
            target_time = dt.datetime.strptime(when, '%H:%M').replace(tzinfo=ZoneInfo(timezone))
            target_time = next_datetime(dt.datetime.now(tz=ZoneInfo(timezone)), target_time.hour, target_time.minute)
        except ValueError:
            await interaction.response.send_message('Error: Malformed time.', ephemeral=True)
        except ZoneInfoNotFoundError:
            await interaction.response.send_message('Error: Malformed timezone.', ephemeral=True)
        else:
            await self._reminder_add(interaction, ReminderType.daily, description, location, target_time)

    @app_commands.command()
    async def display(self, interaction: discord.Interaction):
        """Displays currently set reminders."""
        reminders = await Reminder.filter(user_id=interaction.user.id).order_by('target_time')
        if not reminders:
            await interaction.response.send_message("No reminders set right now.", ephemeral=True)
        else:
            view = ReminderView(reminders)
            embed = view.embed()
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command()
    @app_commands.describe(reminder_id='ID of the reminder you wish to delete')
    async def delete(self, interaction: discord.Interaction, reminder_id: int):
        """Deletes a reminder."""
        deleted = await Reminder.filter(id=reminder_id, user_id=interaction.user.id).delete()
        if deleted:
            await interaction.response.send_message(f"Reminder deleted!", ephemeral=True)
            self._update_reminder_check()
        else:
            await interaction.response.send_message(f"Cannot delete: Reminder does not exist!", ephemeral=True)

    @tasks.loop()
    async def check_reminders(self):
        next_reminder = await Reminder.all().order_by('target_time').first()
        if next_reminder is None:
            self.check_reminders.cancel()
            return
        await discord.utils.sleep_until(next_reminder.target_time)
        reminder = f"<@{next_reminder.user_id}>\n{next_reminder.description}"
        if next_reminder.channel_id:
            channel = self.bot.get_channel(next_reminder.channel_id)
            await channel.send(reminder)
        else:
            user = await self.bot.fetch_user(next_reminder.user_id)
            if await dm_open(user):
                await user.send(reminder)
        if next_reminder.reminder_type.value == next_reminder.reminder_type.daily:
            new_target_time = next_reminder.target_time + dt.timedelta(days=1)
            await Reminder.filter(id=next_reminder.id).update(target_time=new_target_time)
        else:
            await next_reminder.delete()
