import logging
import asyncio

from discord import app_commands, Intents, Interaction, Guild, Member, Status, File
from discord.ext import commands

from os import remove
from threading import Thread
from time import time, sleep

from database import DatabaseManager
from analytics import GraphManager
from yaml import safe_load

from typing import List, Dict


logging.basicConfig()
logging.root.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)


DEBUG: bool = False


class Server:
    """
    Guild parent. Manages values like sweep time.
    """

    SWEEP_INTERVAL: int = 5 # Should be 5 (mins)

    def __init__(self, database_manager: DatabaseManager, guild: Guild, offset: int) -> None:
        self.database_manager: DatabaseManager = database_manager
        self.guild: Guild = guild
        self.next_sweep: int = self.calculate_sweep() + offset * 10

    def calculate_sweep(self) -> int:
        # return time() + self.SWEEP_INTERVAL * 60
        return time() + 0.1 * 60 # <- WARNING: THIS IS DEBUG ONLY! USE THIS FOR REAL: "return time() + self.SWEEP_INTERVAL * 60"
    
    def increment_sweep(self) -> None:
        self.next_sweep += self.calculate_sweep()

    def sweep(self) -> Dict[int, Dict]:
        for member in self.guild.members:
            if member.bot: continue

            if DEBUG and ("captaindeathead" not in member.name): continue

            self.database_manager.add_user(member.id)

            user_data: Dict = self.database_manager.get_user_time_dict(member.id)
            user_simple_time: Dict[str, float] = user_data["simple_time"]

            for activity in member.activities:
                real_activity_name: str = get_real_activity(activity.name)

                activity_time: Dict[str, float] = self.database_manager.get_user_rich_time_dict(member.id, real_activity_name)
                activity_time[member.status.name] += (time() - user_data["last_update"]) / 60

                self.database_manager.update_user_rich_presence_time(member.id, real_activity_name, activity_time)

            user_simple_time[member.status.name] += (time() - user_data["last_update"]) / 60

            self.database_manager.update_user_simple_time(member.id, user_simple_time)

class CommandsManager(commands.Cog):
    """
    Controls all incoming '/' commands and returns the correct response
    """
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @app_commands.command(name="status", description="Test bot is responding.")
    async def ping(self, interaction: Interaction):
        return await interaction.response.send_message("`🟢 Activity bot is online...`")

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

        self.bot.running = True

        logging.info(f"Bot successfully started as {self.bot.user}.")

        self.bot.run_activity_manager()
    
class PresenceManager:
    """
    Tracks the users prescence
    """

    def __init__(self) -> None:
        ...

class SweepManager:
    """
    Waits, and triggers sweeps on each server when the time comes
    """

    def __init__(self, update_servers: callable) -> None:
        self.update_servers: callable = update_servers

        self.servers: List[Server] = update_servers()

        self.thread: Thread = Thread(target=self.main)
        self.alive: bool = True

        self.stopped: bool = False

    def kill(self) -> None:
        self.alive = False

        logging.warning(f"[SWEEP MARKED AS DEAD] Please wait until all servers have been processed...  EST. TIME LEFT: {self.servers[-1].next_sweep - time()}s")

    def main(self) -> None:
        while self.alive:
            self.servers = self.update_servers()

            if len(self.servers) == 0:
                logging.warning("[SWEEP THREAD] Servers list empty! Waiting 10 seconds and trying again...")
                sleep(10)
                continue

            self.servers.sort(key=lambda x: x.next_sweep)

            for server in self.servers:
                next_sweep: int = max(0, server.next_sweep - time())
                
                logging.info(f"[SWEEP THREAD] Sleeping for {next_sweep}s...  (SWEEPING SERVERS {self.servers.index(server)+1}/{len(self.servers)})")
                sleep(next_sweep)

                server.sweep()
                server.increment_sweep()

        self.stopped = True

    def run(self) -> None:
        self.thread.start()

class ActivityManager:
    """
    Tracks the users activity and status
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

        self.guilds: List[Guild] = []
        self.servers: List[Server] = []

        self.ACTIVITY_MATCHES: Dict[str, str] = self._load_activity_matches()

        self.update_servers()

        self.sweep_manager: SweepManager = SweepManager(self.update_servers)

    def _load_activity_matches(self) -> Dict[str, str]:
        ...

    def _load_guilds(self) -> List[Server]:
        servers: List[Server] = []
        
        offset: int = 0
        
        for guild in self.guilds:
            servers.append(Server(self.bot.database_manager, guild, offset))

            offset += 1

        return servers
        
    def fetch_guilds(self) -> List[Guild]:
        logging.info("Updating guilds...")
        
        guilds: List[Guild] = []

        for guild in self.bot.guilds:
            logging.info(f" - Found guild: '{guild.id}'")

            guilds.append(guild)

        return guilds
    
    def update_servers(self) -> List[Server]:
        if len(self.bot.guilds) != len(self.servers):
            self.guilds = self.fetch_guilds()

        self.servers = self._load_guilds()

        return self.servers
    
    def main(self) -> None:
        self.sweep_manager.run()

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

        DEBUG = self.CONFIG['debug']

        intents = Intents.default()
        intents.members = True
        intents.presences = True
        
        super().__init__(intents=intents, command_prefix="^")

        self.database_manager: DatabaseManager = DatabaseManager()

        self.activity_manager: ActivityManager = ActivityManager(self)

        self.running: bool = False

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

    def run_activity_manager(self) -> None:
        self.activity_manager.main()

    def main(self) -> None:
        self.run(self.TOKEN)