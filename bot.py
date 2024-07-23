import logging
import asyncio
from os import remove

from discord import app_commands, Intents, Interaction, Guild, Member, File
from discord.ext import commands

from database import DatabaseManager
from analytics import GraphManager
from yaml import safe_load

from typing import List, Dict


logging.basicConfig()
logging.root.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.NOTSET)


class CommandsManager(commands.Cog):
    """
    Controls all incoming '/' commands and returns the correct response
    """
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @app_commands.command(name="status", description="Test bot is responding.")
    async def ping(self, interaction: Interaction):
        return await interaction.response.send_message("🟢 Activity bot is online...")
    
    @app_commands.command(name="mystatustime", description="Graph of time spent on each status")
    async def statgraph(self, interaction: Interaction, user: Member|None = None):
        if user == None:
            user = interaction.user
        
        username = user.nick
        userid = user.id

        graph = GraphManager.UserOnlineGraph(username=username, userid=userid)
        interaction.response.send_message(file=File(graph))

        remove(graph)
        

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()

        logging.info(f"Bot successfully started as {self.bot.user}.")

        await self.bot.activity_manager.fetch_guilds()
    
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

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

        self.guilds: List[Guild] = asyncio.run(self.fetch_guilds())
        
    def fetch_guilds(self) -> List[Guild]:
        guilds: List[Guild] = []

        for guild in self.bot.guilds:
            logging.info(f"Found guild: '{guild.id}'")

            guilds.append(guild)

        return guilds
    
    def get_members(self, guild_id): ...

class ActivityBot(commands.Bot):
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

        intents = Intents(68608)
        intents.members = True
        
        super().__init__(intents=intents, command_prefix="")

        
        self.activity_manager: ActivityManager = ActivityManager(self)

        asyncio.run(self.__init_cogs())

    async def __init_cogs(self) -> None:
        await self.add_cog(CommandsManager(self))

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
        self.run(self.TOKEN)