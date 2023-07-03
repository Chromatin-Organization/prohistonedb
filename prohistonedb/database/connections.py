""" Defines types for database connections. """
#***===== Imports =====***#
#*----- Standard library -----*#
import abc
from abc import ABC

from typing import Union, Sequence, Mapping, Optional
from collections.abc import Iterable

from pathlib import Path

import sqlite3

import logging

#*----- Flask & Flask Extenstions -----*#
import flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#
from ..types import Field, FieldType

#***===== Type Aliases =====***#
_DatabaseParameters = Union[Sequence, Mapping]
_DatabaseRow = Union[Sequence, Mapping]

#***===== Abstract Base Class 'DatabaseResult' =====***#
class DatabaseResult(ABC, Iterable):
    """ An abstract base class for the results of a database query. """
    #*----- Constructors -----*#
    def __init__(self, **kwargs):
        pass

    #*----- Properties -----*#
    @property
    @abc.abstractmethod
    def description(self) -> Sequence[Sequence]:
        """ Return a sequence with metadata for each column as specified in PEP 249. """

    #*----- Other public functions -----*#
    @abc.abstractmethod
    def fetchone(self) -> _DatabaseRow:
        """ Return the next row in the database result. """

    def fetchmany(self, size: Optional[int] = None) -> Sequence[_DatabaseRow]:
        """ Return the next set of rows in the database result depending on the parameter size. If not supplied the databases default value is used. """

    def fetchall(self) -> Sequence[_DatabaseRow]:
        """ Return all the (remaining) rows in the database result. """

#***===== Abstract Base Class 'DatabaseConnection' =====***#
class DatabaseConnection:
    """ An abstract base class for database connections. Based on PEP 249 and sqlite3. """
    #*----- Constructors -----*#
    @abc.abstractmethod
    def __init__(self, **kwargs):
        """ Prepare the class without setting up the connection. """

    @abc.abstractmethod
    def connect(self):
        """ Open the database connection. """
    
    def __enter__(self):
        self.connect()
        return self
    
    #*----- Destructors -----*#
    @abc.abstractmethod
    def close(self):
        """ Close any existing database connection. """
    
    @abc.abstractmethod
    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        """ Implementing class should handle exceptions before calling 'super()'. """
        self.close()

        #TODO: Add generic error handling !!!
        result = False #* Placeholder for the error handling result
        
        return result
    
    #*----- SQL generation functions -----*#
    @abc.abstractmethod
    def sql_field_type(self, field: Field) -> str:
        """ Returns a string with the SQL database type for the given FieldType. """

    #*----- Other public functions -----*#
    @abc.abstractmethod
    def execute(self, sql:str, parameters: Optional[_DatabaseParameters] = None) -> DatabaseResult:
        """ Execute the supplied SQL query on the database. """
    
    @abc.abstractmethod
    def executemany(self, sql: str, seq_of_parameters: Iterable[_DatabaseParameters]) -> DatabaseResult:
        """ Execute the supplied SQL query for every set of parameters supplied. """

    @abc.abstractmethod
    def commit(self):
        """ Commit any pending queries to the database. """

#***===== SQLiteResult Class =====***#
class SQLiteResult(DatabaseResult):
    #*----- Variable type declarations -----*#
    _cursor: sqlite3.Cursor

    #*----- Constructors -----*#
    def __init__(self, cursor: sqlite3.Cursor):
        self._cursor = cursor

    #*----- Properties -----*#
    @property
    def description(self) -> Sequence[Sequence]:
        return self._cursor.description

    #*----- Other special functions -----*#
    def __iter__(self) -> sqlite3.Cursor:
        return self._cursor.__iter__()
    
    #*----- Other public functions -----*#
    def fetchone(self) -> sqlite3.Row:
        return self._cursor.fetchone()
    
    def fetchmany(self, size: Optional[int] = None) -> list[sqlite3.Row]:
        if size:
            return self._cursor.fetchmany(size)
        else:
            return self._cursor.fetchmany()
    
    def fetchall(self) -> list[sqlite3.Row]:
        return self._cursor.fetchall()

#***===== SQLiteConnection Class =====***#
class SQLiteConnection(DatabaseConnection):
    #*----- Variable type declarations -----*#
    _connection: Union[sqlite3.Connection, None]
    _cursor: Union[sqlite3.Cursor, None]

    #*----- Constructors -----*#
    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._connection = None
        self._cursor = None

    def connect(self):
        """ Opens a database connection. I'd recommend using the 'with' statement, but otherwise don't forget to clean-up with 'close(). """    
        self._connection = sqlite3.connect(database=self._db_path)
        self._connection.row_factory = sqlite3.Row
        self._cursor = self._connection.cursor()
    
    #*----- Destructors -----*#
    def close(self):
        """ Cleans up by closing the database connection. Only necessary if the connection was opened manually with 'connect()'. """
        if self._connection:
            self._connection.close()
            self._connection = None
            self._cursor = None

    def __exit__(self, exc_type, exc_value, traceback):
        result_super = super().__exit__(exc_type, exc_value, traceback)

        #TODO: Add implementation specific error handling!
        result = False #? Placeholder for the error handling result

        return result or result_super
    
    #*----- SQL generation functions -----*#
    @abc.abstractmethod
    def sql_field_type(self, field_type: FieldType) -> str:
        if field_type is FieldType.PRIMARY_TEXT:
            return "TEXT PRIMARY KEY"
        elif field_type is FieldType.PRIMARY_INTEGER:
            return "INTEGER PRIMARY KEY"
        elif field_type in [FieldType.TEXT, FieldType.TEXT_ID, FieldType.IDS]:
            return "TEXT NOT NULL"
        elif field_type in [FieldType.TEXT_OPTIONAL, FieldType.IDS_OPTIONAL]:
            return "TEXT"
        elif field_type in [FieldType.INTEGER, FieldType.INT_ID]:
            return "INTEGER NOT NULL"
        elif field_type is FieldType.TIMESTAMP:
            return "DATETIME NOT NULL"
        else:
            raise ValueError(f"Not implemented for FieldType {field_type}.")

    #*----- Other public functions -----*#
    # ? Add logging to the ABC class?
    def execute(self, sql: str, parameters: Optional[_DatabaseParameters] = None) -> SQLiteResult:
        # Only worry about processing the string manually if it needs to be logged
        if flask.current_app.logger.isEnabledFor(logging.DEBUG):
            sql_str = str(sql)

            # Process any parameters the string may have.
            if not parameters is None:
                try:
                    # Try processing it as a mapping of key-value pairs.
                    for key in parameters.keys():
                        sql_str = sql_str.replace(f":{key}", f"{parameters[key]}")
                except:
                    # If that doesn't work, process it as a list of parameters.
                    for param in parameters:
                        sql_str = sql_str.replace("?", f"{param}", 1)
                
            # Log the SQL used for the query.
            flask.current_app.logger.debug(f"Executing SQL query:\n{sql_str}")

        # Execute the Query on the connection and return the result.
        if parameters is None or len(parameters) == 0:
            return SQLiteResult(self._cursor.execute(sql))
        else:
            return SQLiteResult(self._cursor.execute(sql, parameters))
    
    # ? Add logging to ABC class?
    def executemany(self, sql: str, seq_of_parameters: Iterable[_DatabaseParameters]) -> list[SQLiteResult]:
        flask.current_app.logger.info(f"Using executemany to perform SQL queries...")

        # Only worry about processing the string manually if it needs to be logged
        if flask.current_app.logger.isEnabledFor(logging.DEBUG):
            sql_str = str(sql)
            parameters = seq_of_parameters[0]

            # Process any parameters the string may have.
            if not parameters is None:
                try:
                    # Try processing it as a mapping of key-value pairs.
                    for key in parameters.keys():
                        sql_str = sql_str.replace(f":{key}", f"{parameters[key]}")
                except:
                    # If that doesn't work, process it as a list of parameters.
                    for param in parameters:
                        sql_str = sql_str.replace("?", f"{param}", 1)
                
            # Log the SQL used for the query.
            flask.current_app.logger.debug(f"Executing SQL query with first parameter set:\n{sql_str}")

        # Execute the Query on the connection and return the result.
        if seq_of_parameters is None or len(seq_of_parameters) == 0:
            return [SQLiteResult(cursor) for cursor in self._cursor.executemany(sql)]
        else:
            return [SQLiteResult(cursor) for cursor in self._cursor.executemany(sql, seq_of_parameters)]
    
    def commit(self):
        self._connection.commit()