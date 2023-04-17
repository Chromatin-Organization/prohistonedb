""" All the methods needed for  """
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

#***===== FieldType Enum =====***#
class FieldType(str, Enum):
    """ An enum indicating the field for a search filter. """
    UNIPROT_ID = "uid"
    ORGANISM = "org"
    ORGANISM_ID = "oid"
    SEQUENCE = "seq"
    SEQUENCE_LEN = "seql"
    CATEGORY = "cat"
    LINEAGE = "tax"
    PROTEIN_ID = "pid"
    PROTEOME_ID = "pmid"
    GEN_ID = "gid"
    GENOME_ID = "gmid"

    @property
    def db_name(self) -> str:
        """ Returns the name of the field in the database. """
        return self.name.lower()
    
    @classmethod
    def id_fields(cls) -> list[FieldType]:
        """ Returns all fields that contain IDs. """
        return [cls.UNIPROT_ID, cls.ORGANISM_ID, cls.PROTEIN_ID, cls.PROTEOME_ID, cls.GEN_ID, cls.GENOME_ID]
    
    def sql_condition(self, value: str):
        """ Takes a condition for the field and returns the SQL code for it. """
        if self is self.CATEGORY or self in self.id_fields():
            return f"{self.db_name}='{value}'"
        elif self in [self.ORGANISM, self.SEQUENCE, self.LINEAGE]:
            return f"{self.db_name} LIKE '%{value}%'"
        elif self is self.SEQUENCE_LEN:
            values = [int(val.strip()) for val in value.split("-")]
            return f"{self.db_name} BETWEEN {values[0]} AND {values[1]}"
        else:
            raise NotImplementedError(f"Couldn't generate sql condition for field {self}")
        
    def __repr__(self) -> str:
        return self.value
        
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
        return self._field.sql_condition(self._value)
    
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
        return "[" + ", ".join([filter.__repr__() for filter in self._filters]) + "]"
    
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
        return "[" + ", ".join([filter.__repr__() for filter in self._filters]) + "]"
    
class AnyFilter(OrFilter):
    """ A class for a search filter where any field can match the condition. """
    def __init__(self, value: str):
        """ Take a value to set the condition for the search filter. """
        # TODO: Add validation and type checking.
        self._filters = [Filter(field, value) for field in FieldType.__members__.values() if not field is FieldType.SEQUENCE_LEN]

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
        return f"SELECT * FROM {table}\n  WHERE {filter.sql}"