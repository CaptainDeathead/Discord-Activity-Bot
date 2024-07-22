from discord import Client, Intents, app_commands
import matplotlib as plot


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
        