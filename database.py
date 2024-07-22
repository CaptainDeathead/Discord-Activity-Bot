from pymongo import MongoClient
from pymongo.database import Database


class DatabaseManager:
    """
    Manager for the users database
    """

    def __init__(self) -> None:
        self.db_client: MongoClient = MongoClient("mongodb://localhost:27017/")
        self.db: Database = self.db_client["db"]
        self.users: Database = self.db["users"]

    def test(self) -> None:
        dblist = self.db_client.list_database_names()
        print(dblist)

if __name__ == "__main__":
    dbManager = DatabaseManager()
    dbManager.test()