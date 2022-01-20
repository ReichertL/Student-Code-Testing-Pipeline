import sys
import logging

from util.absolute_path_resolver import resolve_absolute_path

"""
The eval pipline uses an SQLite database. Here the connection to the database is established.
"""

from util.config_reader import ConfigReader
from util.colored_massages import Warn

from sqlalchemy import create_engine, and_, or_
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref, sessionmaker
from database.base import Base
import database.students as s
import database.submissions as sub
import database.runs as r
import database.testcases as tc
from database.testcase_results import TestcaseResult
from database.valgrind_outputs import ValgrindOutput

session=None

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


class DatabaseManager:

    def __init__(self):
        """
        Creates a new database at the location described by the config_database_manager.config at DATABASE_PATH.
        
        Parameters:
            None. Requires file "/resources/config_database_manager.config" exists and has the entry "DATABASE_PATH".
            
        Return:
            Nothing
        
        """
        p=resolve_absolute_path("/resources/config_database_manager.config")
        configuration=ConfigReader().read_file(str(p))
        db_path=resolve_absolute_path(configuration["DATABASE_PATH"])
        engine=create_engine('sqlite:///'+str(db_path), echo=False)
        Base.metadata.create_all(engine, checkfirst=True)
        Session=sessionmaker(bind=engine)
        global session
        session=Session()
        logging.info("Database created/accessed:"+str(db_path))
