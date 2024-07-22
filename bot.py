import discord
from discord import Client, Intents, app_commands
from discord.ext import commands
import matplotlib as plot
import asyncio

class CommandsManager(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.AppCommand()
    async def ping(interaction: discord.Interaction):
        return await interaction.response.send_message("e")

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
        #self.bot = #
        self.intents = Intents(68608)

        await 
