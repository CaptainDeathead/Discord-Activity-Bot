import discord
from discord import Client, Intents, app_commands
from discord.ext import commands
from database import DatabaseManager
import asyncio

class CommandsManager(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.AppCommand()
    async def ping(interaction: discord.Interaction):
        return await interaction.response.send_message("e")
    
class PresenceManager:
    """
    Tracks the users prensence
    """

    def __init__(self) -> None:
        ...

class ActivityManager:
    """
    Tracks the users activity and status
    """


    def __init__(self) -> None:
        ...

class ActivityBot:
    """
    Discord activity bot
    """

    def __init__(self, config_path: str) -> None:
        """
        intents:
            Read Messages / View Channels
            Send Messages
            Read Message History
        """
        
        self.intents = Intents(68608)
        self.bot = commands.Bot(Intents=self.intents)
        self.bot.add_cog(CommandsManager(self.bot))