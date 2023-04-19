import discord

from cogs.shared_views import SphynxView
from utils.constants import COLOR_EMBED_DARK
from .models import Dice


class DiceView(SphynxView):
    def __init__(self, interaction: discord.Interaction, dice: Dice, **kwargs):
        super().__init__(interaction, **kwargs)
        self.dice = dice

    def embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f'{self.dice.dice_count}d{self.dice.face_count}',
            description=f'**Sum of rolled faces**: {self.dice.sum()}\n',
            color=COLOR_EMBED_DARK,
        )
        return embed
