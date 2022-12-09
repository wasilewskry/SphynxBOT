import discord
from discord.ext import commands
from discord.ext import tasks


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def localsync(self, ctx):
        """Syncs slash commands to current guild. Can only be used in a guild."""
        self.bot.tree.copy_global_to(guild=ctx.guild)
        synced = await ctx.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"Synced {len(synced)} commands to this guild.")

    @commands.command()
    @commands.dm_only()
    @commands.is_owner()
    async def globalsync(self, ctx):
        """Syncs slash commands globally. Can only be used in DMs."""
        synced = await ctx.bot.tree.sync()
        await ctx.send(f"Synced {len(synced)} commands globally.")


# -------------------------------------------------------------------------------------------------------------------- #
async def setup(bot):
    await bot.add_cog(Owner(bot))
