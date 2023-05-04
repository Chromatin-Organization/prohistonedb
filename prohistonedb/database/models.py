""" A module defining all the models used in the database. """
#***===== Imports =====***#
#*----- Standard library -----*#
from dataclasses import dataclass
from enum import Enum

from typing import Optional, Union

from pathlib import Path

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#

#***===== Enums =====***#
class Multimer(str, Enum):
    """ An enum for the accepted multimer types. """
    MONOMER = "monomer"
    DIMER = "dimer"
    TETRAMER = "tetramer"
    HEXAMER = "hexamer"

#***===== Base Dataclasses =====***#
@dataclass(eq=False, frozen=True)
class Organism:
    """ A basic dataclass representing an organism. """
    id: str
    name: str

@dataclass(frozen=True)
class Sequence:
    """ A basic dataclass representing an amino acid sequence. """
    value: str

    def __post_init__(self):
        # add uppercase formatting to the sequence.
        object.__setattr__(self, "value", self.value.upper())
    
    def __len__(self) -> int:
        return len(self.value)

@dataclass(eq=False, frozen=True)
class Lineage:
    """ A basic dataclass representing lineage metadata. """
    id: str
    name: str
    rank: str
    hidden: bool = False

#***===== Category Dataclass =====***#
@dataclass(eq=False, frozen=True)
class Category:
    """ A compound dataclass to hold a Category. If no short name is supplied, it will default to the standard name. """
    id: int
    name: str
    preferred_multimer: str
    short_name: Optional[str] = None

    def __post_init__(self):
        # If no short name was supplied, set it to the long name.
        if self.short_name is None:
            object.__setattr__(self, "short_name", self.name)    

@dataclass(eq=False, frozen=True)
class Histone:
    """ A compound dataclass to hold all the metadata for a single histone. """
    uniprot_id: str
    organism: Organism
    sequence: Sequence
    category: Category
    lineage: list[Lineage]
    protein_ids: list[str]
    proteome_ids: Union[list[str], None]
    genes: Union[list[str], None]
    genome_ids: list[str]
    multimers: list[Multimer]
    model_ranking: list[int]
    rel_path: Path
