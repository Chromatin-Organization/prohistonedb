""" All the methods and types needed for building SQL queries. """
#***===== Feature Imports =====***#
from __future__ import annotations

#***===== Imports =====***#
#*----- Standard library -----*#
from enum import Enum

import abc
from abc import ABC

from typing import Iterable, Sequence, Mapping, Optional

from pathlib import Path

#*----- Flask & Flask Extenstions -----*#
import flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#
from ..database.types import FieldType
from ..database.connections import DatabaseConnection, DatabaseResult

#***===== Filter ABC Class ***=====#
class FilterABC(ABC):
    """ An Abstract Base Class for representing search filters. """
    @property
    @abc.abstractmethod
    def _sql_condition(self) -> _SQLCondition:
        """ Returns a _SQL_Condition object that represents the search filter. """

    @property
    @abc.abstractmethod
    def isempty(self) -> bool:
        """ Returns whether the filter is empty. """

    @abc.abstractmethod
    def __repr__(self) -> str:
        pass

#***===== SQL Classes =====***#
class _SQLCondition:
    """ A class representing the condition in an SQL statement. """
    def __init__(self, sql_str: str, parameters: Sequence):
        self.str = sql_str
        self.parameters = parameters  

#TODO: Add tests to see if fields and values are indeed sanitized properly.
class SQL:
    """ A class for storing an SQL query. """
    def __init__(self, table: str, selection: Optional[str] = None, filter: Optional[FilterABC] = None):
        """ Takes in the table name, an optional string representing the fields to be selected and an optional search filter. """
        self._table = table
        if selection is None:
            self._selection = "*"
        else:
            self._selection = selection
        self._condition = filter._sql_condition
    
    def execute(self, database_connection: DatabaseConnection) -> DatabaseResult:
        """Execute the SQL query on the given database connection. """
        query = f"SELECT {self._selection} FROM {self._table}"
        if not self._condition is None:
            query += " WHERE " + self._condition.str

        sql_str = str(query)
        for param in self._condition.parameters:
            sql_str = sql_str.replace("?", f"{param}", 1)
        flask.current_app.logger.debug(f"Generated SQL query: {sql_str}")

        return database_connection.execute(query, parameters=self._condition.parameters)

#***===== Filter Classes =====***#
class Filter(FilterABC):
    """ A class for representing a basic search filter. """
    def __init__(self, field: str, value: str):
        """ Takes a field to be searched and a value to set the search condition. """
        # TODO: Add validation and type checking.
        self._field = FieldType(field)
        self._value = value

    @property
    def _sql_condition(self) -> _SQLCondition:
        field = self._field
        equal_fields = [
            FieldType.UNIPROT_ID,
            FieldType.ORGANISM_ID,
            FieldType.CATEGORY
        ]
        like_fields = [
            FieldType.ORGANISM,
            FieldType.SEQUENCE,
            FieldType.LINEAGE,
            FieldType.PROTEIN_ID,
            FieldType.PROTEOME_ID,
            FieldType.GEN_ID,
            FieldType.GENOME_ID
        ]

        if field in equal_fields:
            return _SQLCondition(f"{field.db_name}=?", [self._value])
        elif field in like_fields:
            return _SQLCondition(f"{field.db_name} LIKE ?", [f"%{self._value}%"])
        elif field is FieldType.SEQUENCE_LEN:
            values = [int(val.strip()) for val in self._value.split("-")]
            return _SQLCondition(f"{field.db_name} BETWEEN ? AND ?", values)
        else:
            raise NotImplementedError(f"Couldn't generate sql condition for field {self}")
    
    @property
    def isempty(self) -> bool:
        return not self._value
    
    def __repr__(self) -> str:
        return f"Filter({self._field}, {self._value})"

class AndFilter(FilterABC):
    """ A class for representing the logical AND combination of two or more search filters. """
    def __init__(self, filters: Iterable[FilterABC]):
        """ Takes in a Iterable of the filters that need to be logically combined. """
        self._filters = filters
    
    @property
    def _sql_condition(self) -> _SQLCondition:
        sql_strings = []
        parameters = []

        for filter in self._filters:
            sql_strings.append(filter._sql_condition.str)
            parameters.extend(filter._sql_condition.parameters)
        
        sql_str = "(" + ") AND (".join(sql_strings) + ")"
        return _SQLCondition(sql_str, parameters)
    
    @property
    def isempty(self) -> bool:
        return all([filter.isempty for filter in self._filters])
    
    def __repr__(self) -> str:
        return "AndFilter([" + ", ".join([filter.__repr__() for filter in self._filters]) + "])"
    
class OrFilter(FilterABC):
    """ A class for representing the logical OR combination of two or more search filters. """
    def __init__(self, filters: Iterable[FilterABC]):
        """ Takes in a Iterable of the filters that need to be logically combined. """
        self._filters = filters
    
    @property
    def _sql_condition(self) -> _SQLCondition:
        sql_strings = []
        parameters = []

        for filter in self._filters:
            sql_strings.append(filter._sql_condition.str)
            parameters.extend(filter._sql_condition.parameters)
        
        sql_str = "(" + ") OR (".join(sql_strings) + ")"
        return _SQLCondition(sql_str, parameters)
    
    @property
    def isempty(self) -> bool:
        return all([filter.isempty for filter in self._filters])
    
    def __repr__(self) -> str:
        return "OrFilter([" + ", ".join([filter.__repr__() for filter in self._filters]) + "])"
    
class AnyFilter(OrFilter):
    """ A class for a search filter where any field can match the condition. """
    def __init__(self, value: str):
        """ Take a value to set the condition for the search filter. """
        # TODO: Add validation and type checking.
        self._filters = [Filter(field, value) for field in FieldType.accepted_fields() if not field is FieldType.SEQUENCE_LEN]

    @property
    def _sql_condition(self) -> str:
        return super()._sql_condition
    
    @property
    def isempty(self) -> bool:
        return super().isempty

    def __repr__(self) -> str:
        return super().__repr__()