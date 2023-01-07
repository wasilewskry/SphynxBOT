import discord
from discord import app_commands
from discord.ext import commands

from run import Sphynx
from .helpers import UnitType, ConversionTable


class UnitCog(commands.GroupCog, group_name='unit'):
    def __init__(self, bot: Sphynx):
        self.bot = bot

    @app_commands.command()
    @app_commands.describe(source_unit='Unit that will be converted',
                           value='Numerical value of the unit',
                           target_unit='Unit that the original will be converted to')
    async def convert(self,
                      interaction: discord.Interaction,
                      source_unit: UnitType,
                      value: float,
                      target_unit: UnitType):
        """Converts units to other units."""
        if source_unit == target_unit:
            await interaction.response.send_message("Same unit selected for source and target.", ephemeral=True)
            return

        if s := ConversionTable.get(source_unit):
            if t := s.get(target_unit):
                converted = round(t(value), 2)
                response = f"``[{source_unit.name}] {value} = {converted} [{target_unit.name}]``"
                await interaction.response.send_message(response, ephemeral=True)
                return

        await interaction.response.send_message(
            f"Cannot convert {source_unit.name} to {target_unit.name}.", ephemeral=True)
