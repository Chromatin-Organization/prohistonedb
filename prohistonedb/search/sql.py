""" All the methods and types needed for building SQL queries. """
#***===== Feature Imports =====***#
from __future__ import annotations

#***===== Imports =====***#
#*----- Standard library -----*#
from enum import Enum

import abc
from abc import ABC

from typing import Iterable, Sequence, Mapping, Optional, Union

from pathlib import Path

#*----- Flask & Flask Extenstions -----*#
import flask

#*----- Flask & Flask Extenstions -----*#
import flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#
from ..database.types import FieldType
from ..database.connections import DatabaseConnection, DatabaseResult

#***===== SQL Condition Class =====***#
class _SQLCondition:
    """ A class representing the condition in an SQL statement. """
    def __init__(self, sql_str: str, parameters: Sequence):
        self.str = sql_str
        self.parameters = parameters 

#***===== Filter Class =====***#
#* The value parameter is currently not sanitized here. Instead, the execute function of the DatabaseConnection takes care of sanitizing it's parameters.
class Filter:
    """ A class for representing a basic search filter. """
    def __init__(self, field: Union[str, FieldType], value: str):
        """ Takes a field to be searched and a value to set the search condition. Is also responsible for input sanitization. """
        self._field = FieldType(field) # Ensure that the supplied field is a valid field type.
        self._value = value 

    @property
    def _sql_condition(self) -> _SQLCondition:
        """ Returns the _SQLCondition that can be used to create an SQL query. """
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
            return _SQLCondition(f"{field.db_name}=?", [self._value])
        elif field in like_fields:
            return _SQLCondition(f"{field.db_name} LIKE ?", [f"%{self._value}%"])
            return _SQLCondition(f"{field.db_name} LIKE ?", [f"%{self._value}%"])
        elif field is FieldType.SEQUENCE_LEN:
            values = [int(val.strip()) for val in self._value.split("-")]
            return _SQLCondition(f"{field.db_name} BETWEEN ? AND ?", values)
            return _SQLCondition(f"{field.db_name} BETWEEN ? AND ?", values)
        else:
            raise NotImplementedError(f"Couldn't generate sql condition for field {self}")
    
    @property
    def isempty(self) -> bool:
        """ Returns whether the filter has a value. """
        return not self._value
    
    def __repr__(self) -> str:
        return f"Filter({self._field}, {self._value})"

#***===== Combined Filter ABC Class ***=====#
class CombinedFilterABC(ABC):
    """ An Abstract Base Class for representing search filters. """

    @abc.abstractmethod
    def __init__(self, filters: Iterable[Filter]) -> None:
        """ Takes in a set of filters, ensures they are valid and stores them in self._filters. Implementers should call this with super() to ensure validation. """
        # Make sure all filters are an instance of Filter to ensure input sanitization.
        for filter in filters:
            if not isinstance(filter, Filter) and not isinstance(filter, CombinedFilterABC):
                raise TypeError(f"'{filter}' is not a valid filter.")
        
        self._filters = filters

    @property
    @abc.abstractmethod
    def _sql_condition(self) -> _SQLCondition:
        """ Returns a _SQL_Condition object that represents the combined search filter. """

    @property
    def isempty(self) -> bool:
        """ Returns whether the filter is empty. """
        return all([filter.isempty for filter in self._filters])
    
    def __repr__(self) -> str:
        return self.__class__.__name__ + "([" + ", ".join([filter.__repr__() for filter in self._filters]) + "])" 

#***===== Combined Filter Classes =====***#
class AndFilter(CombinedFilterABC):
    """ A class for representing the logical AND combination of two or more search filters. """
    def __init__(self, filters: Iterable[Filter]):
        """ Takes in a Iterable of the filters that need to combined with a logical AND. """
        super().__init__(filters)
    
    @property
    def _sql_condition(self) -> _SQLCondition:
        sql_strings = []
        parameters = []

        for filter in self._filters:
            sql_strings.append(filter._sql_condition.str)
            parameters.extend(filter._sql_condition.parameters)
        
        sql_str = "(" + ") AND (".join(sql_strings) + ")"
        return _SQLCondition(sql_str, parameters)

class OrFilter(CombinedFilterABC):
    """ A class for representing the logical OR combination of two or more search filters. """
    def __init__(self, filters: Iterable[Filter]):
        """ Takes in a Iterable of the filters that need to combined with a logical OR. """
        super().__init__(filters)
    
    @property
    def _sql_condition(self) -> _SQLCondition:
        sql_strings = []
        parameters = []

        for filter in self._filters:
            sql_strings.append(filter._sql_condition.str)
            parameters.extend(filter._sql_condition.parameters)
        
        sql_str = "(" + ") OR (".join(sql_strings) + ")"
        return _SQLCondition(sql_str, parameters)
    
class AnyFilter(OrFilter):
    """ A class for a search filter where any field can match the condition. """
    def __init__(self, value: str):
        """ Take a value to set the condition for the search filter. """
        filters = [Filter(field, value) for field in FieldType.accepted_fields() if not field is FieldType.SEQUENCE_LEN]
        super().__init__(filters)

#***===== SQL Class =====***#
class SQL:
    """ A class for storing an SQL query over the search view. """
    def __init__(self, selection: Optional[Sequence[Union[str, FieldType]]] = None, filter: Optional[Union[Filter, CombinedFilterABC]] = None):
        """ Takes in an optional list of fields to be selected and an optional search filter. """
        # Set the view to the dedicated "search" view of the database
        self._VIEW = "search"

        # Handle and sanitize selection input.
        if not selection: # Should handle both None and empty lists.
            self._selection = "*"
        else:
            # Retrieve the database names for the desired fields.
            # Also guarantees that the inputs are valid FieldTypes.
            fields = [FieldType(field).db_name for field in selection]

            # Create the selection string from the database names.
            self._selection = ",".join(fields)

        # Handle and sanitize the filter input.
        if filter is None:
            # In case no filter was provided, leave it at None.
            self._condition = None
        elif isinstance(filter, Filter) or isinstance(filter, CombinedFilterABC):
            # Otherwise ensure that the provided object is an accepted filter for the sake of input sanitization.
            self._condition = filter._sql_condition
        else:
            raise TypeError(f"{filter} does not implement Filter or CombinedFilterABC.")
    
    def execute(self, database_connection: DatabaseConnection) -> DatabaseResult:
        """Execute the SQL query on the given database connection. """
        # Set the basic select statement for the query
        query = f"SELECT {self._selection} FROM {self._VIEW}"

        # Finish early if this query does not have any conditions
        if self._condition is None:
            flask.current_app.logger.debug(f"Generated SQL query: {query}")
            return database_connection.execute(query)
        
        # Otherwise add the conditions to the sql query
        query += " WHERE " + self._condition.str

        # Log the SQL query for debugging
        sql_str = str(query)
        for param in self._condition.parameters:
            sql_str = sql_str.replace("?", f"{param}", 1)
        flask.current_app.logger.debug(f"Generated SQL query: {sql_str}")

        # Execute the SQL query on the database
        return database_connection.execute(query, parameters=self._condition.parameters)