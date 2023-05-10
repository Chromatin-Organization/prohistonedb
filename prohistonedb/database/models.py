""" A module defining all the models used in the database. """
#***===== Imports =====***#
#*----- Standard library -----*#
from dataclasses import dataclass
from enum import Enum

from typing import Optional, Union

from pathlib import Path

#*----- Flask -----*#
import flask

#*----- External packages -----*#
import json

#*----- Custom packages -----*#

#*----- Local imports -----*#
from . import get_categories

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
@dataclass(eq=True, frozen=True)
class Category:
    """ A compound dataclass to hold a Category. If no short name is supplied, it will default to the standard name. """
    id: int
    name: str
    preferred_multimer: Multimer
    short_name: Optional[str] = None

    def __post_init__(self):
        # Make sure that preferred_multimer is a valid Multimer instance
        object.__setattr__(self, "preferred_multimer", Multimer(self.preferred_multimer))
        
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
    multimer_rankings: dict[Multimer, list[int]]
    path: Path

    def __init__(self,
        uniprot_id: str,
        organism_id: str,
        organism: str,
        sequence: str,
        category_id: int,
        lineage_json: str,
        protein_ids: str,
        proteome_ids: str,
        genes: str,
        genome_ids: str,
        ranks: str,
        rel_path: str
    ):
        self.uniprot_id = uniprot_id
        self.organism = Organism(organism_id, organism)
        self.sequence = Sequence(sequence)

        categories = get_categories()
        self.category = categories[category_id]

        lineage_json = json.loads(lineage_json)
        lineage = []
        for item in lineage_json:
            lineage.append(Lineage(item["taxonId"], item["scientificName"], item["rank"], item["hidden"]))

        self.lineage = lineage.reverse()
        self.protein_ids = json.loads(protein_ids)
        self.proteome_ids = json.loads(proteome_ids)
        self.genes = json.loads(genes)
        self.genome_ids = json.loads(genome_ids)

        ranks = json.loads(ranks)
        self.multimer_rankings = {Multimer(multimer):ranks[multimer] for multimer in ranks.keys()}
        self.rel_path = Path(flask.current_app.instance_path) / rel_path 
        
