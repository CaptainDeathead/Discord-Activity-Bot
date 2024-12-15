from pymongo import MongoClient
from pymongo.database import Database
from pymongo.server_api import ServerApi
from pymongo.collection import Collection
from pymongo.cursor import Cursor

from time import time
from copy import deepcopy

from typing import Dict

URI: str = ""

with open("./mongodb_URI.txt", "r") as f:
    URI = f.read()

DEFAULT_USER_STATISTICS: Dict = {
    "last_update": time(),
    "active_session": 0,
    "simple_time": {
        "online": 0,
        "idle": 0,
        "dnd": 0,
        "offline": 0
    },
    "rich_presence_time": {},
    "sessions": {}
}

class DatabaseManager:
    """
    Manager for the users database

    Structure:
        - user id
            - last update time
            - active session id

            - simple time
                - time spent online
                - time spent idle
                - time spent dnd
                - time spent offline
            
            - rich presence time
                - rich presence app
                    - time spent online
                    - time spent idle
                    - time spent dnd
                    - time spent offline

            - sessions
                - session id (user_id followed by session start time)
                    - activity name
                    - status
                    - start time
                    - end time

    There should also be an option for just the past week, or at least make it possible to know when a piece of data is made (Sessions).
    """

    def __init__(self) -> None:
        self.db_client: MongoClient = MongoClient(URI, server_api=ServerApi('1'))
        self.db: Database = self.db_client["db"]
        self.users: Collection = self.db["users"]

    def get_user(self, user_id: int) -> Cursor | None:
        for user in self.users.find({str(user_id): {"$exists": True}}): return user

    def get_user_id(self, username: str) -> int | None:
        for user in self.users.find():
            user_id_str = list(user)[1]
            curr_user_name = user[user_id_str]['username']
            
            if curr_user_name == username:
                return int(user_id_str)
            
        return None

    def get_user_time_dict(self, user_id: int) -> Dict | None:
        user: Cursor | None = self.get_user(user_id)

        if user is None: return None

        return user[str(user_id)]
    
    def get_user_rich_time_dict(self, user_id: int, activity_name: str) -> Dict | None:
        user: Cursor | None = self.get_user(user_id)

        if user is None: return None

        return user[str(user_id)]["rich_presence_time"].get(activity_name, {"online": 0, "idle": 0, "dnd": 0, "offline": 0})

    def get_user_sessions(self, user_id: int) -> Dict | None:
        user: Cursor | None = self.get_user(user_id)

        if user is None: return None

        if "sessions" not in user[str(user_id)]:
            user[str(user_id)]["sessions"] = {}
            user[str(user_id)]["active_session"] = 0

        return user[str(user_id)]["sessions"]

    def add_user(self, user_id: int) -> None:
        if self.get_user(user_id): return

        new_user: Dict = {str(user_id): deepcopy(DEFAULT_USER_STATISTICS)}
        
        self.users.insert_one(new_user)

    def update_user_username(self, user_id: int, username: str) -> None:
        if not self.get_user(user_id): self.add_user(user_id)

        user: Cursor = self.get_user(user_id)
        user_dict: Dict = {str(user_id): user[str(user_id)]}

        user_dict_copy: Dict = deepcopy(user_dict)

        new_user_dict: Dict = {"$set": user_dict_copy}
        new_user_dict["$set"][str(user_id)]["username"] = username

        self.users.update_one(user_dict, new_user_dict)

    def update_user_simple_time(self, user_id: int, status_times: Dict[str, int]) -> None:
        if not self.get_user(user_id): self.add_user(user_id)

        user: Cursor = self.get_user(user_id)
        user_dict: Dict = {str(user_id): user[str(user_id)]}

        user_dict_copy: Dict = deepcopy(user_dict)

        new_user_dict: Dict = {"$set": user_dict_copy}
        new_user_dict["$set"][str(user_id)]["simple_time"] = {
            "online": status_times["online"],
            "idle": status_times["idle"],
            "dnd": status_times["dnd"],
            "offline": status_times["offline"]
        }

        self.users.update_one(user_dict, new_user_dict)

    def update_user_rich_presence_time(self, user_id: int, app_name: str, status_times: Dict[str, int]) -> None:
        if not self.get_user(user_id): self.add_user(user_id)

        user: Cursor = self.get_user(user_id)
        user_dict: Dict = {str(user_id): user[str(user_id)]}
        
        user_dict_copy: Dict = deepcopy(user_dict)
        user_dict_copy[str(user_id)].update({"last_update": time()})

        new_user_dict: Dict = {"$set": user_dict_copy}
        new_user_dict["$set"][str(user_id)]["rich_presence_time"][app_name] = {
            "online": status_times["online"],
            "idle": status_times["idle"],
            "dnd": status_times["dnd"],
            "offline": status_times["offline"]
        }

        self.users.update_one(user_dict, new_user_dict)

    def set_user_last_update(self, user_id: int) -> None:
        if not self.get_user(user_id): self.add_user(user_id)

        user: Cursor = self.get_user(user_id)
        user_dict: Dict = {str(user_id): user[str(user_id)]}

        user_dict_copy = deepcopy(user_dict)
        user_dict_copy[str(user_id)].update({"last_update": time()})

        new_user_dict = {"$set", user_dict_copy}

        self.users.update_one(user_dict, new_user_dict)

    def new_user_session(self, user_id: int, activity_name: str, status: str) -> None:
        if not self.get_user(user_id): self.add_user(user_id)

        user: Cursor = self.get_user(user_id)
        user_dict: Dict = {str(user_id): user[str(user_id)]}
        
        start_time = time()

        active_session_id = int(str(user_id) + str(start_time))

        user_dict_copy: dict = deepcopy(user_dict)
        user_dict_copy[str(user_id)].update({"active_session": active_session_id})

        new_user_dict: Dict = {"$set", user_dict_copy}
        new_user_dict["$set"][str(user_id)]["sessions"][active_session_id] = {
            'activity_name': activity_name,
            'status': status,
            'start_time': start_time,
            'end_time': start_time
        }

        self.users.update_one(user_dict, new_user_dict)

    def update_user_session(self, user_id: int, activity_name: str) -> None:
        if not self.get_user(user_id): self.add_user(user_id)

        user: Cursor = self.get_user(user_id)
        user_dict: Dict = {str(user_id): user[str(user_id)]}

        active_session_id = user_dict[str(user_id)]["active_session"]
        user_sessions = user_dict[str(user_id)]["sessions"]
        active_session = user_sessions["active_session"]

        if active_session["name"] != activity_name:
            raise Exception("Active session name does not match name being updated!")
            return

        user_dict_copy: dict = deepcopy(user_dict)
        
        new_user_dict: Dict = {"$set", user_dict_copy}
        new_user_dict["$set"][str(user_id)]["sessions"][active_session]["end_time"] = time()

        self.users.update_one(user_dict, new_user_dict)

    def delete_database(self) -> None:
        """
        WARNING: THIS ACTION IS VERY DANGEROUS AND SHOULD NOT BE PERFORMED UNDER ALMOST EVERY CIRCUMSTANCE

        PLEASE MAKE SURE YOU HAVE A BACKUP OF THE DATABASE BEFORE YOU PERFORM THIS ACTION OR DATA ***WILL*** BE LOST!
        """

        input("WARNING: THIS ACTION IS VERY DANGEROUS AND SHOULD NOT BE PERFORMED UNDER ALMOST EVERY CIRCUMSTANCE!")
        input("PLEASE MAKE SURE YOU HAVE A BACKUP OF THE DATABASE BEFORE YOU PERFORM THIS ACTION OR DATA ***WILL*** BE LOST!")

        delete: str = input("Press 'y' to confirm database deletion... ")

        if delete == "y":
            self.db.drop_collection("users")

            print("Deleted collection 'users'!")
        else:
            print("Deletion cancelled!")

if __name__ == "__main__":
    dbManager = DatabaseManager()
    #dbManager.add_user(0)
    #dbManager.update_user_simple_time(0, {"online": 10, "idle": 20, "dnd": 30})
    #dbManager.update_user_rich_presence_time(0, "test", {"online": 30, "idle": 20, "dnd": 30})
    for user in dbManager.users.find(): print(user)
    #dbManager.delete_database()
