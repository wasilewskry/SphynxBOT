import discord
from discord import app_commands
from discord.ext import commands

from utils.unit_definitions import UnitType, ConversionTable


class Unit(commands.GroupCog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    @app_commands.command()
    @app_commands.describe(source_unit='Type of unit that needs to be converted',
                           value='Numerical value of the unit',
                           target_unit='Type of unit you want original unit to be converted to')
    async def convert(self, interaction: discord.Interaction,
                      source_unit: UnitType,
                      value: float,
                      target_unit: UnitType):
        """Converts units to other units."""
        if source_unit == target_unit:
            await interaction.response.send_message("Same unit selected for source and target.", ephemeral=True)
            return

        if s := ConversionTable.get(source_unit, None):
            if t := s.get(target_unit, None):
                converted = round(t(value), 2)
                response = f"[{source_unit.name}] {value} = **{converted}** [{target_unit.name}]"
                await interaction.response.send_message(response, ephemeral=True)
                return

        await interaction.response.send_message(f"Cannot convert {source_unit.name} to {target_unit.name}.",
                                                ephemeral=True)


# -------------------------------------------------------------------------------------------------------------------- #
async def setup(bot: commands.Bot):
    await bot.add_cog(Unit(bot))
