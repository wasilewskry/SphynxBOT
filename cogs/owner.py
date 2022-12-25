from discord.ext import commands


class Owner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def globalsync(self, ctx: commands.Context):
        """Syncs slash commands globally"""
        synced = await ctx.bot.tree.sync()
        await ctx.send(f"Synced {len(synced)} commands globally.")

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def localsync(self, ctx: commands.Context):
        """Syncs slash commands to current guild"""
        synced = await ctx.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"Synced {len(synced)} commands to this guild.")


# -------------------------------------------------------------------------------------------------------------------- #
async def setup(bot: commands.Bot):
    await bot.add_cog(Owner(bot))
