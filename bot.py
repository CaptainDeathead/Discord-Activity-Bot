import logging
import asyncio

from discord import app_commands, activity, Intents, Interaction, Guild, Message, Member, Status, File
from discord.ext import commands

from os import remove, execv
from sys import executable, argv
from threading import Thread
from time import time, sleep

from database import DatabaseManager
from analytics import GraphManager
from yaml import safe_load
from json import loads as parse_json

from webserver import WebServer

from typing import List, Dict


logging.basicConfig()
logging.root.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)


DEBUG: bool = False


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
        global DEBUG

        self.CONFIG: Dict = self._load_cfg(config_path)
        self.TOKEN: str = self.__get_token()

        DEBUG = self.CONFIG['debug']
        self.RESTART_HOUR_TIMER = self.CONFIG['restart_hour_timer']
        self.ENABLE_WEBSERVER = self.CONFIG['enable_webserver']
        
        if self.ENABLE_WEBSERVER:
            self.WEBSERVER_PORT = self.CONFIG['webserver_port']

        intents = Intents.default()
        intents.members = True
        intents.presences = True
        
        super().__init__(intents=intents, command_prefix="^")

        self.database_manager: DatabaseManager = DatabaseManager()
        self.activity_manager: ActivityManager = ActivityManager(self)
        self.graph_manager: GraphManager = GraphManager(self.database_manager)
        
        if self.ENABLE_WEBSERVER:
            self.web_server: Thread = Thread(target=lambda: WebServer(self.graph_manager, self.WEBSERVER_PORT))
            self.web_server.start()
        
        self.running: bool = False
        self.init_time = time()

        asyncio.run(self.__init_cogs())

    async def __init_cogs(self) -> None:
        await self.add_cog(CommandsManager(self, self.graph_manager))

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

class Server:
    """
    Guild parent. Manages values like sweep time.
    """

    SWEEP_INTERVAL: int = 1 # Should be 5 (mins)

    def __init__(self, database_manager: DatabaseManager, guild: Guild, offset: int, get_real_activity: callable) -> None:
        self.database_manager: DatabaseManager = database_manager
        self.guild: Guild = guild
        self.get_real_activity: callable = get_real_activity

    def sweep(self) -> Dict[int, Dict]:
        for member in self.guild.members:
            if member.bot: continue

            if DEBUG and ("captaindeathead" not in member.name): continue

            self.database_manager.add_user(member.id)

            user_data: Dict = self.database_manager.get_user_time_dict(member.id)
            user_simple_time: Dict[str, float] = user_data["simple_time"]

            if time() - user_data["last_update"] > 60 * 20: # if the user has not been updated in the last 20 mins, do not update in case of bot crash
                user_data["last_update"] = time()
            
            used_active_sessions = []

            for activity in member.activities:
                if activity.name is None: continue

                real_activity_name: str = self.get_real_activity(activity.name)

                if real_activity_name == "": continue

                activity_time: Dict[str, float] = self.database_manager.get_user_rich_time_dict(member.id, real_activity_name)
                activity_time[member.status.name] += (time() - user_data["last_update"]) / 60

                self.database_manager.update_user_rich_presence_time(member.id, real_activity_name, activity_time)

                # Session updating
                ret_status, session_id = self.database_manager.update_user_session(member.id, real_activity_name, member.status.name)
                used_active_sessions.append(session_id)

                if ret_status == False: # Activity not present
                    self.database_manager.new_user_session(member.id, real_activity_name, member.status.name)

            for session_id in self.database_manager.get_active_sessions(member.id):
                if session_id not in used_active_sessions:
                    self.database_manager.remove_active_session_id(member.id, session_id)

            user_simple_time[member.status.name] += (time() - user_data["last_update"]) / 60

            self.database_manager.update_user_simple_time(member.id, user_simple_time)
            self.database_manager.update_user_username(member.id, member.name)
            self.database_manager.set_user_last_update(member.id) # Very important

class CommandsManager(commands.Cog):
    """
    Controls all incoming '/' commands and returns the correct response
    """
    
    def __init__(self, bot: ActivityBot, graph_manager: GraphManager) -> None:
        self.bot: ActivityBot = bot

        self.graph_manager: GraphManager = graph_manager

    @app_commands.command(name="bot_status", description="Test bot is responding.")
    async def ping(self, interaction: Interaction):
        logging.info("Recieved 'ping' command...")

        return await interaction.response.send_message("`🟢 Activity bot is online...`")
    
    @app_commands.command(name="help", description="Get instructions on how to use the bot.")
    async def help(self, interaction: Interaction):
        logging.info("Recieved 'help' command...")

        return await interaction.response.send_message("Type '`/simple_status`' to view your basic Discord status. Provide another user to view them instead\nType '`/rich_status`' for more in-depth information regarding your activities. Provide another user to view them instead.\n ~ To view more information about each presence provide text in the '`presence`' argument. This will search for the closest presence to that query and show information about it.")

    @app_commands.command(name="simple_status", description="Graph of time spent on each basic status")
    async def simple_status_graph(self, interaction: Interaction, user: Member | None = None):
        await interaction.response.defer()

        logging.info("Recieved 'simple_status' command...")

        if user is None:
            user = interaction.user
        
        username = user.name
        user_id = user.id

        graph_file: str = self.graph_manager.get_user_simple_time(user_id, username)

        if graph_file == "":
            await interaction.followup.send(f"{username} is not found in the database. Please DM @captaindeathead for assistance.")
        else:
            await interaction.followup.send(file=File(graph_file))

        remove(graph_file)

    @app_commands.command(name="server_simple_status", description="Graph of time spent in the server.")
    async def server_simple_status(self, interaction: Interaction):
        await interaction.response.defer()

        logging.info("Recieved 'server_simple_status' command...")

        user = interaction.user
        server = interaction.guild
        server_name = server.name

        if server is None:
            return await interaction.followup.send("Server not found.")

        member_list = []
        for member in server.members:
            if not member.bot: member_list.append(member.id)

        if len(member_list) == 0:
            return await interaction.followup.send("Guild info not found!")

        graph_file = self.graph_manager.get_server_simple_time(member_list, server_name)

        if graph_file == "":
            return await interaction.followup.send("Unknown error - Graph file not found!\nThis is likely because an error occured during the graphs creation.")

        await interaction.followup.send(file=File(graph_file))

        remove(graph_file)

    @app_commands.command(name="rich_status", description="Graph of time spent on a users rich presence.")
    async def rich_status_graph(self, interaction: Interaction, user: Member | None = None, presence: str | None = None):
        await interaction.response.defer()

        logging.info("Recieved 'rich_status' command...")

        if user == None:
            user = interaction.user
        
        username = user.name
        user_id = user.id

        if isinstance(presence, str):
            graph_file: str = self.graph_manager.get_user_rich_time_specific(user_id, username, presence)
        else:
            graph_file: str = self.graph_manager.get_user_rich_time(user_id, username)

        if graph_file == "":
            await interaction.followup.send(f"{username} is not found in the database. Please DM @captaindeathead for assistance.")
            return
        elif graph_file == "no_best_activity":
            await interaction.followup.send(f"'{presence}' was not found in {username}'s rich activities! Try a different query (Type '/help' for info).")
            return
        else:
            await interaction.followup.send(file=File(graph_file))

        remove(graph_file)

    @app_commands.command(name="rich_status_table", description="Table of time spent on a users rich presence.")
    async def rich_status_table(self, interaction: Interaction, user: Member | None = None):
        await interaction.response.defer()

        logging.info("Recieved 'rich_status_table' command...")

        if user == None:
            user = interaction.user
        
        username = user.name
        user_id = user.id

        table: str = self.graph_manager.get_user_rich_time_table(user_id, username)

        if table == "":
            await interaction.followup.send(f"{username} is not found in the database. Please DM @captaindeathead for assistance.")
            return
        elif table == "user_no_status":
            await interaction.followup.send(f"{username} has no status's recorded.")
            return
        else:
            await interaction.followup.send("Note: If you are on desktop, click on the image and select `Open in browser` to zoom in.", file=File(table))

        remove(table)

    @app_commands.command(name="server_rich_status", description="Graph / table of time a server spends on each rich presence.")
    async def rich_server_graph(self, interaction: Interaction, table: bool = False):
        await interaction.response.defer()

        logging.info(f"Recieved 'server_rich_status' command...")

        user = interaction.user
        server = interaction.guild
        server_name = server.name

        if server is None:
            return await interaction.followup.send("Server not found.")

        member_list = []
        for member in server.members:
            if not member.bot: member_list.append(member.id)
        
        if member_list == []:
            return await interaction.followup.send("Guild info not found!")
        
        if table:
            return_filename = self.graph_manager.get_server_rich_time_table(member_list, server_name)
        else:
            return_filename = self.graph_manager.get_server_rich_time(member_list, server_name)

        if return_filename == "":
            return await interaction.followup.send("Unknown error - Graph file not found!\nThis is likely because an error occured during the graphs creation.")
        
        if table:
            await interaction.followup.send("Note: If you are on desktop, click on the image and select `Open in browser` to zoom in.", file=File(return_filename))
        else:
            await interaction.followup.send(file=File(return_filename))

        remove(return_filename)

    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        if time() - self.bot.init_time >= self.bot.RESTART_HOUR_TIMER * 60 * 60: # 2 hours = 2 * 60 mins * 60 secs
            logging.warning("Bot is restarting... Reason: Time since bot initialization > 2 hours! Command: \"execv(executable, ['python'] + argv)\". Waiting 5 mins before proceding...")
            
            self.bot.init_time = time()
            await asyncio.sleep(60*5) # wait 5 mins before restart
            await execv(executable, ['python'] + argv)

    @commands.Cog.listener()
    async def on_ready(self):
        if self.bot.running: return

        await self.bot.tree.sync()

        self.bot.running = True

        logging.info(f"Bot successfully started as {self.bot.user}.")

        await self.bot.change_presence(status=Status.online, activity=activity.CustomActivity("Type '/help' for more info."))

        self.bot.run_activity_manager()

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

        logging.warning(f"[SWEEP MARKED AS DEAD] Please wait until all servers have been processed...  EST. TIME LEFT: 60s")

    def main(self) -> None:
        while self.alive:
            self.servers = self.update_servers()

            if len(self.servers) == 0:
                logging.warning("[SWEEP THREAD] Servers list empty! Waiting 10 seconds and trying again...")
                sleep(10)
                continue

            for server in self.servers:
                server.sweep()
                next_sweep: int = 60            

                logging.info(f"[SWEEP THREAD] Sleeping for {next_sweep}s...  (SWEEPING SERVERS {self.servers.index(server)+1}/{len(self.servers)})")
                sleep(next_sweep)

        self.stopped = True

    def run(self) -> None:
        self.thread.start()

class ActivityManager:
    """
    Tracks the users activity and status
    """

    def __init__(self, bot: ActivityBot) -> None:
        self.bot: ActivityBot = bot

        self.guilds: List[Guild] = []
        self.servers: List[Server] = []

        self.ACTIVITY_MATCHES: Dict[str, str] = self._load_activity_matches()

        self.update_servers()

        self.sweep_manager: SweepManager = SweepManager(self.update_servers)

    def _load_activity_matches(self) -> Dict[str, str]:
        with open(self.bot.CONFIG["activity_matches_path"], "r") as activity_matches_file:
            return parse_json(activity_matches_file.read())

    def _load_guilds(self) -> List[Server]:
        servers: List[Server] = []
        
        offset: int = 0
        
        for guild in self.guilds:
            servers.append(Server(self.bot.database_manager, guild, offset, self.get_real_activity))

            offset += 1

        return servers
    
    def get_real_activity(self, activity_name: str) -> str:
        return self.ACTIVITY_MATCHES.get(activity_name, activity_name)
        
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
