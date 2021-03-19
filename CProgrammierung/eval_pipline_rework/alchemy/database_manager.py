import sys
import logging

from util.absolute_path_resolver import resolve_absolute_path
from util.config_reader import ConfigReader
from util.colored_massages import Warn


from sqlalchemy import create_engine, and_, or_
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref, sessionmaker
from alchemy.base import Base 
import alchemy.students as s
import alchemy.submissions as sub
import alchemy.runs as r
import alchemy.testcases as tc
from alchemy.testcase_results import Testcase_Result
from alchemy.valgrind_outputs import Valgrind_Output

session=None

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT,level=logging.DEBUG)

class DatabaseManager:

      

    def __init__(self):
        p = resolve_absolute_path("/resources/config_database_manager.config")
        configuration = ConfigReader().read_file(str(p))
        db_path=resolve_absolute_path(configuration["DATABASE_PATH"])
        #db_path=":memory:"
        engine = create_engine('sqlite:///'+str(db_path), echo = False)
        Base.metadata.create_all(engine, checkfirst=True)      
        Session = sessionmaker(bind = engine)
        global session
        session = Session()
        logging.info("Database created/accessed:"+str(db_path))


 
 
    def functionality(self):
        pass
       
        
        
        
        
        
        

        

       
       
       
       
       
       
       
       
       
       
        

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        

        
        




        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        



















