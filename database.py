from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.cursor import Cursor

from time import time
from copy import deepcopy

from typing import Dict

DEFAULT_USER_STATISTICS: Dict = {
    "last_update": time(),
    "simple_time": {
        "online": 0,
        "idle": 0,
        "dnd": 0,
        "offline": 0
    },
    "rich_presence_time": {}
}

class DatabaseManager:
    """
    Manager for the users database

    Structure:
        - user id
            - last update time

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

    There should also be an option for just the past week, or at least make it possible to know when a piece of data is made.
    """

    def __init__(self) -> None:
        self.db_client: MongoClient = MongoClient("mongodb://localhost:27017/")
        self.db: Database = self.db_client["db"]
        self.users: Collection = self.db["users"]

    def get_user(self, user_id: int) -> Cursor | None:
        for user in self.users.find({str(user_id): {"$exists": True}}): return user

    def get_user_time_dict(self, user_id: int) -> Dict | None:
        user: Cursor | None = self.get_user(user_id)

        if user is None: return None

        return user[str(user_id)]
    
    def get_user_rich_time_dict(self, user_id: int, activity_name: str) -> Dict | None:
        user: Cursor | None = self.get_user(user_id)

        if user is None: return None

        return user[str(user_id)]["rich_presence_time"].get(activity_name, {"online": 0, "idle": 0, "dnd": 0, "offline": 0})

    def add_user(self, user_id: int) -> None:
        if self.get_user(user_id): return

        new_user: Dict = {str(user_id): deepcopy(DEFAULT_USER_STATISTICS)}
        
        self.users.insert_one(new_user)

    def update_user_simple_time(self, user_id: int, status_times: Dict[str, int]) -> None:
        if not self.get_user(user_id): self.add_user(user_id)

        user: Cursor = self.get_user(user_id)

        user_dict: Dict = {str(user_id): user[str(user_id)]}

        user_dict_copy: Dict = deepcopy(user_dict)
        user_dict_copy[str(user_id)].update({"last_update": time()})

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