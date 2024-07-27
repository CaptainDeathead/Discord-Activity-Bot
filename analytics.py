import matplotlib.pyplot as plot

from typing import Dict, List, Tuple

from database import DatabaseManager

class GraphManager:
    """
    Manages all the graph drawing and visualisations of the user data
    """

    COLORS: Dict[str, Tuple[int, int, int]] = {
        "white": (1, 1, 1),
        "red": (1, 0, 0),
        "yellow": (.9, .9, 0),
        "green": (0, 1, 0),
        "blue": (0, 0, 1),
        "grey": (.5, .5, .5),
        "black": (0, 0, 0)
    }

    def __init__(self, database_manager: DatabaseManager) -> None:
        self.dbManager: DatabaseManager = database_manager

    def format_time(self, percent: float, time_list: List[float]) -> str:
        absolute = int(round(percent / 100. * sum(time_list)))

        hours: int = absolute // 60
        mins: int = absolute % 60

        return f"{percent:.1f}%\n({hours}h {mins}m)"

    def get_user_simple_time(self, user_id: int, username: str) -> str:
        user_data = self.dbManager.get_user(user_id)

        if user_data is None: return

        simple_time: Dict[str, int] = user_data[str(user_id)]["simple_time"]

        time_list: List[int] = [int(time) for time in simple_time.values()]
        
        labels = ["Online", "Idle", "Do Not Disturb", "Offline"]
        colors = [self.COLORS["green"], self.COLORS["yellow"], self.COLORS["red"], self.COLORS["grey"]]

        file_name: str = f"{user_id}_simple_times.png"

        plot.pie(time_list, labels=labels, colors=colors, autopct=lambda percent: self.format_time(percent, time_list))
        plot.title(f"{username}'s basic status breakdown")
        plot.savefig(file_name)
        plot.close()

        return file_name
        # remember to delete the file once sent