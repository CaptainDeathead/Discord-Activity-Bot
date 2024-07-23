import matplotlib.pyplot as plot
from database import DatabaseManager
import numpy

class GraphManager:
    def __init__(self) -> None:
        pass

    def UserOnlineGraph(self, userid, username) -> str:
        data = DatabaseManager.get_user(userid)
        times = numpy.array([data["simple_time"]["online"][1]], [data["simple_time"]["idle"][1]], [data["simple_time"]["dnd"][1]])
        labels = ["Online", "Idle", "Do Not Disturb"]
        colors = ["green", "yellow", "red"]

        plot.pie(times, labels, colors)
        plot.title(f"{username}'s status times.")
        plot.savefig(f"{userid}online.png")
        plot.close()

        return f"{userid}online.png"
        #remember to delete the file once sent