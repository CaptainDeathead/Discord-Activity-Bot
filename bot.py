import discord
from discord import Client, Intents, app_commands
from discord.ext import commands
from database import DatabaseManager
import asyncio

from yaml import safe_load

from typing import Dict

class CommandsManager(commands.Cog):
    """
    Controls all incoming '/' commands and returns the correct response
    """
    
    def __init__(self, bot) -> None:
        self.bot = bot
        #synced = self.bot.tree.sync()

    @app_commands.command(name="ping", description="Test bot is responding.")
    async def ping(self, interaction: discord.Interaction):
        return await interaction.response.send_message("e")
    

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Bot successfully started as {self.bot.user}.")
    
class PresenceManager:
    """
    Tracks the users prescence
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

        self.CONFIG: Dict = self._load_cfg(config_path)
        self.TOKEN: str = self.__get_token()
        
        self.intents = Intents(68608)
        self.bot = commands.Bot(intents=self.intents, command_prefix="") 

        asyncio.run(self.__init_cogs())

    async def __init_cogs(self) -> None:
        await self.bot.add_cog(CommandsManager(self.bot))
        
        #self.bot.tree.sync()

    def __get_token(self) -> str:
        try:
            with open(self.CONFIG["token_path"], "r") as token_raw:
                return token_raw.read()

        except FileNotFoundError:
            print("Error while loading token!\nPlease ensure the path to the token in the config file is correct.")
            exit()

        except UnicodeError:
            print("Error while loading token!\nPlease ensure the token file is 'utf-8' encoding and has no special characters.")

        except Exception as e:
            print(f"Error while loading token!\nError: {str(e)}!")

    def _load_cfg(self, path: str) -> Dict:
        with open(path, "r") as cfg:
            return safe_load(cfg.read())

    def main(self) -> None:
        self.bot.run(self.TOKEN)#