""" Defines types for database connections. """
#***===== Imports =====***#
#*----- Standard library -----*#
import abc
from abc import ABC

from typing import Union, Sequence, Mapping, Optional
from collections.abc import Iterable

from pathlib import Path

import sqlite3

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#

#***===== Type Aliases =====***#
_DatabaseParameters = Union[Sequence, Mapping]
_DatabaseRow = Union[Sequence, Mapping]

#***===== Abstract Base Class 'DatabaseResult' =====***#
class DatabaseResult(ABC, Iterable):
    """ An abstract base class for the results of a database query. """
    #*----- Constructors -----*#
    def __init__(self, **kwargs):
        pass

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
        self._connection = sqlite3.connect(database=self._db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
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
    
    #*----- Other public functions -----*#
    def execute(self, sql: str, parameters: Optional[_DatabaseParameters] = None) -> SQLiteResult:
        if parameters is None:
            return SQLiteResult(self._cursor.execute(sql))
        else:
            return SQLiteResult(self._cursor.execute(sql, parameters))
    
    def executemany(self, sql: str, seq_of_parameters: Iterable[_DatabaseParameters]) -> list[SQLiteResult]:
        return [DatabaseResult(cursor) for cursor in self._cursor.executemany(sql, seq_of_parameters)]
    
    def commit(self):
        self._connection.commit()