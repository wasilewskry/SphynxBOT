import discord

from cogs.shared_views import SphynxView
from utils.constants import COLOR_EMBED_DARK
from .models import Dice


class DiceView(SphynxView):
    def __init__(
            self,
            interaction: discord.Interaction,
            dice: Dice,
            success_threshold: int | None = None,
            **kwargs
    ):
        super().__init__(interaction, **kwargs)
        self.dice = dice
        self.success_threshold = success_threshold

    def embed(self) -> discord.Embed:
        breakdown = '\n'.join(
            [f'**{face}s**: {count}' for face, count in sorted(self.dice.most_recent_roll.items(), reverse=True)]
        )
        if self.success_threshold:
            successes = self.dice.successes(self.success_threshold)
            color = discord.Color.green() if successes else discord.Color.red()
        else:
            color = COLOR_EMBED_DARK
        embed = discord.Embed(
            title=f'{self.dice.dice_count}d{self.dice.face_count}',
            description=f'**Sum of rolled faces**: {self.dice.sum()}\n',
            color=color,
        )
        if self.success_threshold:
            embed.set_footer(text=f'Success at {self.success_threshold}+')
            embed.description += f'**Successes**: {successes}'
        embed.add_field(name='Dice breakdown', value=breakdown)
        return embed
