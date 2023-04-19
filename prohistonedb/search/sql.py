""" All the methods and types needed for building SQL queries. """
#! FIXME: To prevent sql injection we may want to use another method then format strings.

#***===== Feature Imports =====***#
from __future__ import annotations

#***===== Imports =====***#
#*----- Standard library -----*#
from enum import Enum

import abc
from abc import ABC

from typing import Iterable

from pathlib import Path

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#
from ..database.types import FieldType
        
#***===== Filter Classes ***=====#
class FilterABC(ABC):
    """ An Abstract Base Class for representing search filters. """
    @property
    @abc.abstractmethod
    def sql(self) -> str:
        """ Returns the SQL code that represents the search filter. """

    @property
    @abc.abstractmethod
    def isempty(self) -> bool:
        """ Returns whether the filter is empty. """

    @abc.abstractmethod
    def __repr__(self) -> str:
        pass

    def and_filter(self, other: FilterABC) -> AndFilter:
        """ Returns a AndFilter that combines this filter with another. """
        return AndFilter([self, other])
    
    def or_filter(self, other: FilterABC) -> OrFilter:
        """ Returns a OrFilter that combines this filter with another. """
        return OrFilter([self, other])

class Filter(FilterABC):
    """ A class for representing a basic search filter. """
    def __init__(self, field: str, value: str):
        """ Takes a field to be searched and a value to set the search condition. """
        # TODO: Add validation and type checking.
        self._field = FieldType(field)
        self._value = value

    @property
    def sql(self) -> str:
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
            return f"{field.db_name}='{self._value}'"
        elif field in like_fields:
            return f"{field.db_name} LIKE '%{self._value}%'"
        elif field is FieldType.SEQUENCE_LEN:
            values = [int(val.strip()) for val in self._value.split("-")]
            return f"{field.db_name} BETWEEN {values[0]} AND {values[1]}"
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
    def sql(self) -> str:
        return "(" + ") AND (".join([filter.sql for filter in self._filters]) + ")"
    
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
    def sql(self) -> str:
        return "(" + ") OR (".join([filter.sql for filter in self._filters]) + ")"
    
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
    def sql(self) -> str:
        return super().sql
    
    @property
    def isempty(self) -> bool:
        return super().isempty

    def __repr__(self) -> str:
        return super().__repr__()
    
#***===== Function Definitions =====***#
def build_sql(table: str, filter: FilterABC):
    """ Returns SQL code for running a query on a given database under a filter. """
    if filter.isempty:
        return f"SELECT * FROM {table}"
    else:
        return f"SELECT * FROM {table} WHERE {filter.sql}"