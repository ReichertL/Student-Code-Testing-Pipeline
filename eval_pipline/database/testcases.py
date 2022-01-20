"""
SQL Alchemy classed used to create table "Testcase". Also contains functions that query the database for table "Testcase".
Testcases are used for evaluating a submissions and can be used to test different types of behaviour.
     GOOD testcases: Students code should produce correct result for this testcase.
     BAD testcases: Students code should fail gracefully for this testcase.
     BAD_OR_OUTPUT: Students code should either produce the correct output or fail gracefully.
     PERFORMANCE: Testcases for performance evaluation. TODO not fully implemented.
     UNSPECIFIED: If type of testcase could not be concerned when parsing the corresponding files.
"""

import logging
from sqlalchemy import *
from database.base import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression
import database.database_manager as dbm

FORMAT="[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


class Testcase(Base):
    __tablename__='Testcase'
    # GOOD testcases: Students code should produce correct result for this testcase. 
    # BAD testcases: Students code should fail gracefully for this testcase.
    # BAD_OR_OUTPUT: Students code should either produce the correct output or fail gracefully.
    # PERFORMANCE: Testcases for performance evaluation. TODO not fully implemented.
    # UNSPECIFIED: If type of testcase could not be concerned when parsing the corresponding files.
    type_options=["GOOD", "BAD", "PERFORMANCE", "BAD_OR_OUTPUT", "PERFORMANCE", "UNSPECIFIED"]

    # Columns for the table "Testcase"
    id=Column(Integer, primary_key=True)
    path=Column(String, nullable=False)
    valgrind_needed=Column(Boolean, default=True, server_default=expression.true())
    short_id=Column(String, nullable=False, unique=True)
    description=Column(String, nullable=False)
    hint=Column(String, nullable=False)
    type=Column(String,
                nullable=False)  # Descibes what the expected outcome of the testcase is. Either GOOD, BAD or BAD_OR_OUTPUT
    rlimit=Column(Integer)
    testcase_results=relationship("TestcaseResult")

    def __init__(self, path, short_id, description, hint, type, rlimit):
        if type not in self.type_options:
            raise TypeError("Type of Testcase does not have an allowed value. Was "+str(type)+" but only "+str(
                self.type_options)+" are allowed.")
        self.path=path
        self.short_id=short_id
        self.description=description
        self.hint=hint
        self.rlimit=rlimit
        self.type=type

    def __repr__(self):
        return ("(Testcase: "+str(self.id)+","+
                str(self.short_id)+","+
                str(self.description)+","+
                str(self.hint)+","+
                str(self.rlimit)+","+
                str(self.type)+","+
                str(self.path)+
                ")")

    def update(self, path, short_id, description, hint, type, valgrind_needed, rlimit):
        """
        Update a testcase object. Does not commit to database! 
        Parameters:
            path (string): path to testcase
            short_id (string): short name of testcase
            description (string): description of testcase
            hint (string) : Hint used for creating mails for students
            type (string) : Describes what the expected outcome of the testcase is. Either GOOD, BAD or BAD_OR_OUTPUT
            valgrind_needed (bool): If it is necessary to check valgrind output for this testcase.
            rlimit (int):  the memory limit for this testcase
        Returns:
            Nothing
        """
        self.path=path
        self.valgrind_needed=valgrind_needed
        self.short_id=short_id
        self.description=description
        self.hint=hint
        self.type=type
        self.rlimit=rlimit

    @classmethod
    def create_or_update(cls, path, short_id, description, hint, type, valgrind=True, rlimit=None):
        """
        Updates testcase or creates it if it does not exist in the database. 
        Checks by using path,short_id, description, hint, type, valgrind_needed, and rlimit.
        
        Parameters:
            path (string): path to testcase
            short_id (string): short name of testcase
            description (string): description of testcase
            hint (string) : Hint used for creating mails for students
            type (string) : Describes what the expected outcome of the testcase is. Either GOOD, BAD or BAD_OR_OUTPUT
            valgrind_needed (bool): If it is necessary to check valgrind output for this testcase. Optional.
            rlimit (int): The memory limit for this testcase. Optional.
        Returns:
            Nothing
        """

        tc_exists=dbm.session.query(Testcase).filter(Testcase.short_id==short_id, Testcase.path==path,
                                                     Testcase.valgrind_needed==valgrind,
                                                     Testcase.description==description, Testcase.hint==hint,
                                                     Testcase.type==type, Testcase.rlimit==rlimit).count()
        if tc_exists==0:
            similar=dbm.session.query(Testcase).filter(Testcase.short_id==short_id).first()
            if similar is not None:
                similar.update(path, short_id, description, hint, type, valgrind, rlimit)
                dbm.session.commit()
            else:
                new_testcase=Testcase(path, short_id, description, hint, type, rlimit)
                new_testcase.valgrind_needed=valgrind
                dbm.session.add(new_testcase)
                dbm.session.commit()
            logging.info("New testcase inserted or altered one updated.")

    @classmethod
    def get_all(cls):
        """
        Returns all testcases.
        Parameters:None
        Returns:
            List of Testcase objects
        """
        testcases=dbm.session.query(Testcase).all()
        return testcases

    @classmethod
    def get_all_bad(cls):
        """
        Returns all testcases with type "BAD".
        Parameters:None
        Returns:
            List of Testcase objects
        """
        testcases=dbm.session.query(Testcase).filter(Testcase.type=="BAD").all()
        return testcases

    @classmethod
    def get_all_good(cls):
        """
        Returns all testcases with type "GOOD".
        Parameters:None
        Returns:
            List of Testcase objects
        """
        testcases=dbm.session.query(Testcase).filter_by(type="GOOD").all()
        return testcases

    @classmethod
    def get_all_bad_or_output(cls):
        """
        Returns all testcases with type "BAD_OR_OUTPUT".
        Parameters:None
        Returns:
            List of Testcase objects
        """
        testcases=dbm.session.query(Testcase).filter_by(type="BAD_OR_OUTPUT").all()
        return testcases

    @classmethod
    def get_all_performance(cls):
        """
        Returns all testcases with type "PERFORMANCE".
        Parameters:None
        Returns:
            List of Testcase objects
        """
        testcases=dbm.session.query(Testcase).filter_by(type="PERFORMANCE").all()
        return testcases

    @classmethod
    def get_by_id(id):
        """
        Returns a testcase given a testcase ID
        Parameters:
            id (int) : ID of the testcase
        Returns:
            Single Testcase objects or None if ID does not exist.
        """
        testcase=dbm.session.query(Testcase).filter(Testcase.id==id).first()
        return testcase

    @classmethod
    def get_by_short_id(short_id):
        """
        Returns a testcase given a testcase short IDs.
        Parameters:
            short_id (string) : name of the testcase
        Returns:
            Single Testcase objects or None if short ID not found.
        """
        testcase=dbm.session.query(Testcase).filter(Testcase.short_id==short_id).first()
        return testcase
