""" A module defining custom types that are used by prohistonedb. """
#***===== Feature Imports =====***#
from __future__ import annotations

#***===== Imports =====***#
#*----- Standard library -----*#
from enum import Enum
from typing import Sequence, Union, Mapping

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
    
#***===== ResultCounts Class =====***#
@dataclass(eq=False, frozen=True)
class ResultCounts:
    total: int
    categories: pd.Series[int]
    superkingdoms: pd.Series[int]
    max_seq_len: int

    def __init__(self, results: Sequence[Union[Sequence, Mapping]], columns: Sequence[str]):
        def find_superkingdom(lineage_json: str) -> Union[str, None]:
            superkingdoms = [item["scientificName"] for item in json.loads(lineage_json) if item["rank"] == "superkingdom"]

            if len(superkingdoms) == 0:
                return None
            elif len(superkingdoms) == 1:
                return superkingdoms[0]
            else:
                raise ValueError("Multiple superkingdoms found.")              

        df = pd.DataFrame.from_records(results, columns=columns)
        categories = df["category"] \
            .value_counts(sort=False) \
            .sort_index(na_position="last")
        superkingdoms = df["lineage_json"] \
            .apply(find_superkingdom) \
            .value_counts(sort=False, dropna=False) \
            .sort_index(na_position="last")
        
        if len(df["sequence_len"]) == 0:
            max_seq_len = 0
        else:
            max_seq_len = df["sequence_len"].max()
        
        object.__setattr__(self, "total", len(results))
        object.__setattr__(self, "categories", categories)
        object.__setattr__(self, "superkingdoms", superkingdoms)
        object.__setattr__(self, "max_seq_len", max_seq_len)