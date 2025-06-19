import matplotlib.pyplot as plot
import plotly.graph_objects as go

from time import time
from random import uniform
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

    DISPLAY_STATUS: Dict[str, str] = {
        "online": "Online",
        "idle": "Idle",
        "dnd": "Do Not Disturb",
        "offline": "Offline"
    }

    def __init__(self, database_manager: DatabaseManager) -> None:
        self.dbManager: DatabaseManager = database_manager
        plot.rcParams['text.color'] = 'white'

    def _random_color(self) -> Tuple[int, int, int]:
        return (uniform(0, 1), uniform(0, 1), uniform(0, 1))
    
    def _search_list(self, str_list: List[str], query: str) -> str:
        best_string: str = ""
        best_score: int = 100000
        for string in str_list:
            if query.lower() not in string.lower(): continue

            score: int = 0

            score += len(string) - len(query) # how close in length the words are (also gives them negative if string is short than query)
            
            if score < best_score:
                best_score = score
                best_string = string

        return best_string

    def get_user_id(self, username: str) -> int | None:
        return self.dbManager.get_user_id(username)
    
    def remove_minority_keys(self, dictionary: Dict[any, int]) -> List[str]:
        total: int = sum(dictionary.values())
        new_str_list: List[str] = []

        for label in dictionary:
            if dictionary[label] / total < 0.01:
                new_str_list.append(" ")
            else:
                new_str_list.append(label)

        return new_str_list
    
    def remove_minority_items(self, str_list: List[str], value_list: List[int]) -> List[str]:
        total: int = sum(value_list)
        new_str_list: List[str] = []

        for i, label in enumerate(str_list):
            if value_list[i] / total < 0.01:
                new_str_list.append(" ")
            else:
                new_str_list.append(label)

        return new_str_list

    def format_time(self, percent: float, time_list: List[float]) -> str:
        if percent < 5: return ""
        
        absolute = int(round(percent / 100. * sum(time_list)))

        hours: int = absolute // 60
        mins: int = absolute % 60

        return f"{percent:.1f}%\n({hours}h {mins}m)"

    def get_user_simple_time(self, user_id: int, username: str) -> str:
        user_data = self.dbManager.get_user(user_id)

        if user_data is None: return ""

        simple_time: Dict[str, int] = user_data[str(user_id)]["simple_time"]

        time_list: List[int] = [int(time) for time in simple_time.values()]
        
        labels: Tuple[str] = ("Online", "Idle", "Do Not Disturb", "Offline")
        colors: Tuple[Tuple[int, int, int]] = (self.COLORS["green"], self.COLORS["yellow"], self.COLORS["red"], self.COLORS["grey"])

        file_name: str = f"{user_id}_simple_times.png"

        plot.pie(time_list, labels=labels, colors=colors, autopct=lambda percent: self.format_time(percent, time_list))
        plot.title(f"{username}'s basic status breakdown")
        plot.savefig(file_name, facecolor='none')
        plot.close()

        return file_name
        # remember to delete the file once sent

    def get_user_rich_time(self, user_id: int, username: str) -> str:
        user_data = self.dbManager.get_user(user_id)

        if user_data is None: return ""

        activities: Dict[str, Dict] = user_data[str(user_id)]["rich_presence_time"]
        activity_names: List[str] = []
        activity_times: List[int] = []
        colors: List[Tuple[int, int, int]] = []

        for activity in activities:
            activity_names.append(activity)
            activity_times.append(sum(activities[activity].values()))
            colors.append(self._random_color())

        file_name: str = f"{user_id}_rich_times.png"

        plot.pie(activity_times, labels=self.remove_minority_items(activity_names, activity_times),
                 colors=colors, autopct=lambda percent: self.format_time(percent, activity_times))
        plot.title(f"{username}'s rich status breakdown")
        plot.savefig(file_name, facecolor='none')
        plot.close()

        return file_name
        # remember to delete the file once sent

    def get_user_rich_time_table(self, user_id: int, username: str) -> str:
        user_data = self.dbManager.get_user(user_id)

        if user_data is None: return ""

        activities: Dict[str, Dict] = user_data[str(user_id)]["rich_presence_time"]
        activity_names: List[str] = []
        activity_times: List[int] = []

        for activity in activities:
            activity_names.append(activity)
            activity_times.append(round(sum(activities[activity].values()) / 60, 2))

        if len(activity_names) == 0:
            return "user_no_status"

        sorted_pairs = sorted(zip(activity_times, activity_names), reverse=True)
        sorted_activity_times, sorted_activity_names = zip(*sorted_pairs)

        ranks = list(range(1, len(activity_names)+1))
        names = list(sorted_activity_names)
        hours = list(sorted_activity_times)

        ranks.append("-")
        names.append("Total")
        hours.append(sum(activity_times))

        fig = go.Figure(
            data=[go.Table(header=dict(values=["Rank", "Name", "Hours"]),
            cells=dict(values=[ranks, names, hours]))
        ])

        estimated_height = 400 + max(0, (len(activity_names) - 10) * 30)

        file_name: str = f"{user_id}_rich_times_table.png"
        fig.write_image(file_name, height=estimated_height)

        return file_name
        # remember to delete the file once sent

    def get_user_rich_time_specific(self, user_id: int, username: str, query: str) -> str:
        user_data = self.dbManager.get_user(user_id)

        if user_data is None: return ""

        activities: Dict[str, Dict] = user_data[str(user_id)]["rich_presence_time"]
        best_activity: str = self._search_list(activities, query)

        if best_activity == "": return "no_best_activity"

        simple_time: Dict[str, int] = user_data[str(user_id)]["rich_presence_time"][best_activity]
        time_list: List[int] = [int(time) for time in simple_time.values()]
        
        labels: Tuple[str] = ("Online", "Idle", "Do Not Disturb", "Offline")
        colors: Tuple[Tuple[int, int, int]] = (self.COLORS["green"], self.COLORS["yellow"], self.COLORS["red"], self.COLORS["grey"])

        file_name: str = f"{user_id}_rich_custom_times.png"

        plot.pie(time_list, labels=labels, colors=colors, autopct=lambda percent: self.format_time(percent, time_list))
        plot.title(f"{username}'s rich status for '{best_activity}' breakdown")
        plot.savefig(file_name, facecolor='none')
        plot.close()

        return file_name
        # remember to delete the file once sent

    def get_server_simple_time(self, members: list, server_name: str) -> str:
        server_statuses: Dict[str, int] = {"Online": 0, "Idle": 0, "Do Not Disturb": 0, "Offline": 0}
        colors: Tuple[Tuple[int, int, int]] = (self.COLORS["green"], self.COLORS["yellow"], self.COLORS["red"], self.COLORS["grey"])
        file_name: str = f'{server_name.replace(" ", "_")}_server_simple.png'

        for user_id in members:
            user_time_data = self.dbManager.get_user_time_dict(user_id)

            if user_time_data is None: return ""

            user_statuses = user_time_data["simple_time"]

            for status in user_statuses:
                server_statuses[self.DISPLAY_STATUS[status]] += user_statuses[status]
        
        plot.pie(server_statuses.values(), labels=self.remove_minority_keys(server_statuses),
                 colors=colors, autopct=lambda percent: self.format_time(percent, server_statuses.values()))
        plot.title(f"{server_name}'s simple status breakdown")
        plot.savefig(file_name, facecolor='none')
        plot.close()

        return file_name
    
    def get_server_rich_time(self, members: list, server_name: str) -> str:
        server_activities: Dict[str, int] = {}
        colors: List[Tuple[int, int, int]] = []
        file_name: str = f'{server_name.replace(" ", "_")}_server_rich.png'

        for user_id in members:
            user_data = self.dbManager.get_user(user_id)

            if user_data is None: return ""

            activities: Dict[str, Dict] = user_data[str(user_id)]["rich_presence_time"]

            for activity in activities:
                if activity in server_activities:
                    server_activities[activity] += sum(activities[activity].values())
                else:
                    server_activities[activity] = sum(activities[activity].values())
                    colors.append(self._random_color())
        
        plot.pie(server_activities.values(), labels=self.remove_minority_keys(server_activities),
                 colors=colors, autopct=lambda percent: self.format_time(percent, server_activities.values()))
        plot.title(f"{server_name}'s rich status breakdown")
        plot.savefig(file_name, facecolor='none')
        plot.close()

        return file_name

    def get_server_rich_time_table(self, members: list, server_name: str) -> str:
        file_name: str = f'{server_name.replace(" ", "_")}_server_rich_table.png'

        activity_names = []
        activity_times = []

        for user_id in members:
            user_data = self.dbManager.get_user(user_id)

            if user_data is None: return ""

            activities: Dict[str, Dict] = user_data[str(user_id)]["rich_presence_time"]

            for activity in activities:
                activity_time = round(sum(activities[activity].values()) / 60, 2)
                
                if activity not in activity_names:
                    activity_names.append(activity)
                    activity_times.append(activity_time)
                else:
                    index = activity_names.index(activity)
                    activity_times[index] = round(activity_times[index] + activity_time, 2)

        sorted_pairs = sorted(zip(activity_times, activity_names), reverse=True)
        sorted_activity_times, sorted_activity_names = zip(*sorted_pairs)

        ranks = list(range(1, len(activity_names)+1))
        names = list(sorted_activity_names)
        hours = list(sorted_activity_times)

        ranks.append("-")
        names.append("Total")
        hours.append(sum(activity_times))

        fig = go.Figure(
            data=[go.Table(header=dict(values=["Rank", "Name", "Hours"]),
            cells=dict(values=[ranks, names, hours]))
        ])

        estimated_height = 400 + max(0, (len(activity_names) - 10) * 30)

        file_name: str = f"{server_name}_rich_times_table.png"
        fig.write_image(file_name, height=estimated_height)

        return file_name
        # remember to delete the file once sent
