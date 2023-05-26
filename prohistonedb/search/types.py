""" A module defining all the types used for processing user input during searches. """
#***===== Feature Imports =====***#
from __future__ import annotations

#***===== Imports =====***#
#*----- Standard library -----*#
from enum import Enum
from typing import Union, Sequence, Mapping
from dataclasses import dataclass

import json

#*----- External packages -----*#
import pandas as pd

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
    PROTEIN_IDS = "pid"
    PROTEOME_IDS = "pmid"
    GENES = "gen"
    GENOME_IDS = "gmid"
    
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
    
    def __str__(self) -> str:
        return self.name.lower().replace("_", " ").replace("id", "ID").capitalize()
    
@dataclass(eq=False, frozen=True)
class ResultCounts:
    total: int
    categories: pd.Series[int]
    lineages: pd.Series[int]


    def __init__(self, results: Sequence[Union[Sequence, Mapping]], columns: Sequence[str]):
        def try_value (list: Sequence, idx: int) -> Union[str, None]:
            try:
                return list[idx]
            except:
                return None
        
        df = pd.DataFrame.from_records(results, columns=columns)
        df["superkingdom"] = df["lineage_json"].apply(lambda l:
            try_value([item["scientificName"] for item in json.loads(l) if item["rank"] == "superkingdom"], 0)
        )
        object.__setattr__(self, "total", len(results))
        object.__setattr__(self, "categories", df["category"].value_counts())
        object.__setattr__(self, "lineages", df["superkingdom"].value_counts())