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
    "last_online": time(),
    "active_sessions": [],
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
            - last online time
            - active session's id's

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
                        - online
                        - idle
                        - dnd
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
        user_dict: Dict = {str(user_id): user[str(user_id)]}

        if user is None: return None

        if "sessions" not in user_dict[str(user_id)] or "active_sessions" not in user_dict[str(user_id)]:
            self.add_sessions_field(user_id)

        return user_dict[str(user_id)]["sessions"]

    def get_active_sessions(self, user_id: int) -> list[str]:
        user: Cursor | None = self.get_user(user_id)
        user_dict: Dict = {str(user_id): user[str(user_id)]}

        if user is None: return None
        if "active_sessions" not in user_dict[str(user_id)]:
            self.add_sessions_field(user_id)

        return user_dict[str(user_id)]["active_sessions"]

    def add_user(self, user_id: int) -> None:
        if self.get_user(user_id): return

        new_user: Dict = {str(user_id): deepcopy(DEFAULT_USER_STATISTICS)}
        
        self.users.insert_one(new_user)

    def add_sessions_field(self, user_id: int) -> None:
        if not self.get_user(user_id): self.add_user(user_id)

        user: Cursor = self.get_user(user_id)
        user_dict: Dict = {str(user_id): user[str(user_id)]}

        user_dict_copy: Dict = deepcopy(user_dict)

        new_user_dict: Dict = {"$set": user_dict_copy}
        new_user_dict["$set"][str(user_id)]["active_sessions"] = []
        new_user_dict["$set"][str(user_id)]["sessions"] = {}

        self.users.update_one(user_dict, new_user_dict)

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

        new_user_dict: Dict = {"$set": user_dict_copy}
        new_user_dict["$set"][str(user_id)]["rich_presence_time"][app_name] = {
            "online": status_times["online"],
            "idle": status_times["idle"],
            "dnd": status_times["dnd"],
            "offline": status_times["offline"]
        }

        self.users.update_one(user_dict, new_user_dict)

    def get_user_last_online(self, user_id: int) -> None:
        if not self.get_user(user_id): self.add_user(user_id)

        user: Cursor = self.get_user(user_id)
        user_dict: Dict = {str(user_id): user[str(user_id)]}

        if "last_online" not in user_dict[str(user_id)]:
            self.set_user_last_online(user_id, time())

            user: Cursor = self.get_user(user_id)
            user_dict: Dict = {str(user_id): user[str(user_id)]}

        return user_dict[str(user_id)]["last_online"]

    def set_user_last_online(self, user_id: int, online_time: float) -> None:
        if not self.get_user(user_id): self.add_user(user_id)

        user: Cursor = self.get_user(user_id)
        user_dict: Dict = {str(user_id): user[str(user_id)]}

        user_dict_copy = deepcopy(user_dict)
        user_dict_copy[str(user_id)].update({"last_online": online_time})

        new_user_dict = {"$set": user_dict_copy}

        self.users.update_one(user_dict, new_user_dict)

    def get_user_last_update(self, user_id: int) -> float:
        if not self.get_user(user_id): self.add_user(user_id)

        user: Cursor = self.get_user(user_id)
        user_dict: Dict = {str(user_id): user[str(user_id)]}

        return user_dict[str(user_id)]["last_update"]

    def set_user_last_update(self, user_id: int) -> None:
        if not self.get_user(user_id): self.add_user(user_id)

        user: Cursor = self.get_user(user_id)
        user_dict: Dict = {str(user_id): user[str(user_id)]}

        if "last_online" not in user_dict[str(user_id)]:
            self.set_user_last_online(user_id, time())

        user_dict_copy = deepcopy(user_dict)
        user_dict_copy[str(user_id)].update({"last_update": time()})

        new_user_dict = {"$set": user_dict_copy}

        self.users.update_one(user_dict, new_user_dict)

    def new_user_session(self, user_id: int, activity_name: str, status: str) -> str:
        if not self.get_user(user_id): self.add_user(user_id)

        user: Cursor = self.get_user(user_id)
        user_dict: Dict = {str(user_id): user[str(user_id)]}
        
        start_time = time()

        active_session_id = str(user_id) + str(start_time)

        #print(f"New user session: {user_id=}, {activity_name=}, {status=}")

        if "sessions" not in user_dict[str(user_id)] or "active_sessions" not in user_dict[str(user_id)]:
            self.add_sessions_field(user_id)

        user_dict_copy: dict = deepcopy(user_dict)

        active_sessions = user_dict_copy[str(user_id)]["active_sessions"]
        active_sessions.append(active_session_id)

        user_dict_copy[str(user_id)].update({"active_sessions": active_sessions})

        new_user_dict: Dict = user_dict_copy
        new_user_dict[str(user_id)]["sessions"][active_session_id] = {
            'name': activity_name,
            'status': {
                'online': 0,
                'idle': 0,
                'dnd': 0
            },
            'start_time': start_time,
            'end_time': start_time
        }
        new_user_dict: Dict = {"$set": new_user_dict}

        self.users.update_one(user_dict, new_user_dict)
        self.update_user_session(user_id, activity_name, status)

        return active_session_id

    def remove_active_session_id(self, user_id: int, session_id: str) -> None:
        if not self.get_user(user_id): self.add_user(user_id)

        user: Cursor = self.get_user(user_id)
        user_dict: Dict = {str(user_id): user[str(user_id)]}

        active_sessions = self.get_active_sessions(user_id)
        if session_id in active_sessions:
            active_sessions.remove(session_id)

        user_dict_copy = deepcopy(user_dict)

        new_user_dict: Dict = user_dict_copy
        new_user_dict[str(user_id)]["active_sessions"] = active_sessions
        new_user_dict: Dict = {"$set": user_dict_copy}

        self.users.update_one(user_dict, new_user_dict)

    def update_user_session(self, user_id: int, activity_name: str, status: str) -> tuple[bool, str]:
        # Returns:
        #  - True -> status is good
        #  - False -> status is not good

        #print(f"Updating user session for: {user_id=}, {activity_name=}, {status=}")

        if not self.get_user(user_id): self.add_user(user_id)

        user: Cursor = self.get_user(user_id)
        user_dict: Dict = {str(user_id): user[str(user_id)]}

        if "sessions" not in user_dict[str(user_id)] or "active_sessions" not in user_dict[str(user_id)]:
            self.add_sessions_field(user_id)

        active_sessions = user[str(user_id)]["active_sessions"]
        user_sessions = user_dict[str(user_id)]["sessions"]

        active_session_id = ""

        for session_id in active_sessions:
            session = user_sessions[session_id]

            if session["name"] == activity_name:
                active_session_id = session_id
                break
            
        if active_session_id == "":
            return False, ""

        user_dict_copy: dict = deepcopy(user_dict)

        last_update = user_dict_copy[str(user_id)]["last_update"]

        new_user_dict = user_dict_copy
        
        new_user_dict[str(user_id)]["sessions"][active_session_id]["end_time"] = time()
        new_user_dict[str(user_id)]["sessions"][active_session_id]["status"][status] += (time() - last_update) / 60

        new_user_dict: Dict = {"$set": user_dict_copy}

        self.users.update_one(user_dict, new_user_dict)

        #print(f"Updating user session for: {user_id=}, {activity_name=}, {status=} -- Success!")

        return True, active_session_id

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
