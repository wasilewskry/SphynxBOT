import discord


async def dm_open(user: discord.User) -> bool:
    """Checks if user accepts DMs. Hacky."""
    try:
        await user.send()
    except discord.HTTPException as e:
        if e.code == 50006:
            return True
        elif e.code == 50007:
            return False
        else:
            raise
