from discord import Client, Intents, app_commands
from database import DatabaseManager
import asyncio

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

class CommandsManager:
    """
    Controls all incoming '/' commands and returns the correct response
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