import matplotlib.pyplot as plot
import numpy as np

from database import DatabaseManager



class GraphManager:
    def __init__(self) -> None:
        pass

    def UserOnlineGraph(self, userid, username) -> str:
        data = DatabaseManager.get_user(userid)
        times = np.array([data["simple_time"]["online"]], [data["simple_time"]["idle"]], [data["simple_time"]["dnd"]])
        labels = ["Online", "Idle", "Do Not Disturb"]
        colors = ["green", "yellow", "red"]

        plot.pie(times, labels, colors)
        plot.title(f"{username}'s status times.")
        plot.savefig(f"{userid}online.png")
        plot.close()

        return f"{userid}online.png"
        # remember to delete the file once sent