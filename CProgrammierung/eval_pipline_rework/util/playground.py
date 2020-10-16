from sqlalchemy import create_engine
from sqlalchemy.orm import relationship, backref, sessionmaker
from alchemy.database_manager import DatabaseManager 

class Playground:
    name: str
      

    def __init__(self):
        self.name = "Playground"


    @staticmethod
    def functionality():
        print("Debug env to test new functionality which can be implemented, called or composed here")
        db_manager=DatabaseManager()
        print(db_manager.is_empty())
        db_manager.functionality()


    def run(self):
        self.functionality()
        


















