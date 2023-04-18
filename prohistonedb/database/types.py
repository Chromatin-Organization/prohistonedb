""" Defines types needed for the metadata database. """
#***===== Feature Imports =====***#
from __future__ import annotations

#***===== Imports =====***#
#*----- Standard Library -----*#
from enum import Enum

#*----- Flask & Flask Extenstions -----*#
import flask

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
    
    @classmethod
    def accepted_fields(cls) -> list[str]:
        """ Returns all the str values that are accepted as field types. """
        return list(cls.__members__.values())
    
    @property
    def db_name(self) -> str:
        """ Returns the name of the field in the database. """
        return self.name.lower()
        
    def __repr__(self) -> str:
        return self.value