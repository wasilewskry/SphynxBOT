import discord
from discord import app_commands
from discord.ext import commands

from run import Sphynx
from .models import Dice
from .views import DiceView


class DiceCog(commands.GroupCog, group_name='dice'):
    def __init__(self, bot: Sphynx):
        self.bot = bot

    @app_commands.command()
    @app_commands.describe(
        amount='How many dice you want to throw. (1-100)',
        faces='How many faces on each dice. (2-100)',
        success_threshold='Minimal value of a face to be considered a success.',
        ephemeral='Whether the roll is hidden or visible for other users.'
    )
    async def roll(
            self,
            interaction: discord.Interaction,
            amount: int,
            faces: int,
            success_threshold: int | None = None,
            ephemeral: bool = False,
    ):
        """Rolls dice."""
        if not 1 <= amount <= 100:
            await interaction.response.send_message('Error: Invalid amount of dice.', ephemeral=True)
        elif not 2 <= faces <= 100:
            await interaction.response.send_message('Error: Invalid amount of faces.', ephemeral=True)
        else:
            dice = Dice(amount, faces)
            dice.roll()
            view = DiceView(interaction, dice, success_threshold)
            embed = view.embed()
            await interaction.response.send_message(view=view, embed=embed, ephemeral=ephemeral)
