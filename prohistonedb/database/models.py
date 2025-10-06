""" A module defining all the models used in the database. """
#***===== Imports =====***#
#*----- Standard library -----*#
from dataclasses import dataclass
from enum import Enum

from typing import Optional, Union

from pathlib import Path

import functools
import datetime

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#

#***===== Enums =====***#
@functools.total_ordering
class Multimer(str, Enum):
    """ An enum for the accepted multimer types. """
    MONOMER = "monomer"
    DIMER = "dimer"
    TETRAMER = "tetramer"
    HEXAMER = "hexamer"

    def __str__(self) -> str:
        return self.value

    def __lt__(self, other) -> bool:
        if self is self.MONOMER:
            if other is self.MONOMER:
                return False
            else:
                return True
        elif self is self.DIMER:
            if (other is self.MONOMER) or (other is self.DIMER):
                return False
            else:
                return True
        elif self is self.TETRAMER:
            if other is self.HEXAMER:
                return True
            else:
                return False
        elif self is self.HEXAMER:
            return False
        else:
            raise ValueError(f"Unknown multimer {self}")

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
@dataclass(eq=True, frozen=True)
class Category:
    """ A compound dataclass to hold a Category. If no short name is supplied, it will default to the standard name. """
    id: int
    name: str
    preferred_multimer: Multimer
    has_page: bool
    short_name: Optional[str] = None

    def __post_init__(self):
        # Make sure that preferred_multimer is a valid Multimer instance
        object.__setattr__(self, "preferred_multimer", Multimer(self.preferred_multimer))
        
        # If no short name was supplied, set it to the long name.
        if self.short_name is None:
            object.__setattr__(self, "short_name", self.name)
    
    @property
    def static_logo_path(self):
        return (Path("logo-data") / self.name).with_suffix(".json").as_posix()
    
    @property
    def static_phylotree_path(self):
        return (Path("phylotrees") / self.name).with_suffix(".xml").as_posix()
            
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
    gene_names: list[str]
    genome_ids: list[str]
    pdb_ids: list[str]
    multimer_rankings: dict[Multimer, list[int]]
    publications: Union[list[str], None]
    rel_path: Path
    last_updated: datetime.datetime

    @property
    def multimers(self) -> list[Multimer]:
        multimers = list(self.multimer_rankings.keys())
        multimers.sort()
        return multimers
    
    def has_multimer(self, multimer: Multimer) -> bool:
        return multimer in self.multimer_rankings.keys()
    
    def get_model_id(self, multimer: Multimer, rank: int) -> int:
        return self.multimer_rankings[multimer][rank-1]

    def get_path(self, multimer: Multimer) -> Path:
        path = Path("data") / self.rel_path
        if multimer != multimer.MONOMER:
            path = path / f"{self.uniprot_id}_{multimer.value}"
        else:
            path = path / self.uniprot_id
        return path

    def get_cif_path(self, multimer: Multimer, rank: int) -> Path:
        path = self.get_path(multimer)
        model = self.get_model_id(multimer,rank)

        if multimer is Multimer.HEXAMER:
            relaxed = "unrelaxed"
        else:
            relaxed = "relaxed"
        
        # Account for difference in filename between monomers & other multimers
        if multimer is Multimer.MONOMER:
            path_section = "ptm"
        else:
            path_section = "multimer_v3"

        return path / f"{self.uniprot_id}_{relaxed}_rank_00{rank}_alphafold2_{path_section}_model_{model}_seed_000.cif"