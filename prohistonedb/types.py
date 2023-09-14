""" A module defining custom types that are used by prohistonedb. """
#***===== Feature Imports =====***#
from __future__ import annotations

#***===== Imports =====***#
#*----- Standard library -----*#
import enum
from enum import Enum
from typing import Sequence, Union, Mapping

from dataclasses import dataclass

from collections import Counter

import json

#*----- Flask & Flask extenstions -----*#
import flask

#*----- Other external packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#

#***===== ComparisonType Enum =====***#
class ComparisonType(Enum):
    """ An enum representing what type of SQL comparison a field uses in an SQL query. """
    EQUAL = enum.auto()
    LIKE = enum.auto()
    BETWEEN = enum.auto()

#***===== FieldType Enum =====***#
class FieldType(Enum):
    """ An enum representing the datatype of a field. """
    PRIMARY_INTEGER = enum.auto()
    PRIMARY_TEXT = enum.auto()
    INTEGER = enum.auto()
    TEXT = enum.auto()
    TEXT_OPTIONAL = enum.auto()
    INT_ID = enum.auto()
    TEXT_ID = enum.auto()
    IDS = enum.auto()
    IDS_OPTIONAL = enum.auto()
    TIMESTAMP = enum.auto()

    @classmethod
    def optional_types(cls) -> set[FieldType]:
        return {
            cls.TEXT_OPTIONAL,
            cls.IDS_OPTIONAL
        }
    
    @classmethod
    def required_types(cls) -> set[FieldType]:
        return {field_type for field_type in FieldType} - FieldType.optional_types()

#***===== Field Enum =====***#
class Field(str, Enum):
    """ An enum indicating the field for a search filter. """
    # Searchable
    UNIPROT_ID = "uid"
    ORGANISM = "org"
    ORGANISM_ID = "oid"
    CATEGORY = "cat"
    SEQUENCE = "seq"
    LINEAGE = "tax"
    PROTEIN_IDS = "pid"
    PROTEOME_IDS = "pmid"
    GENES = "gen"
    GENOME_IDS = "gmid"

    # Facet
    CATEGORY_ID = "cid"
    SEQUENCE_LEN = "seql"
    LINEAGE_SUPERKINGDOM = "sup"

    # Wildcard
    ANY = "any"

    @classmethod
    def accepted_fields(cls) -> set[str]:
        """ Returns all the str values that are accepted as field types. """
        return set(cls.__members__.values())
    
    @classmethod
    def search_fields(cls) -> set[Field]:
        """ Return a list of possible search fields. """
        return {
            cls.UNIPROT_ID,
            cls.ORGANISM,
            cls.ORGANISM_ID,
            cls.CATEGORY,
            cls.SEQUENCE,
            cls.LINEAGE,
            cls.PROTEIN_IDS,
            cls.PROTEOME_IDS,
            cls.GENES,
            cls.GENOME_IDS
        }

    @classmethod
    def facet_fields(cls) -> set[Field]:
        """ Return a list of possible facet fields. """
        return {
            cls.CATEGORY_ID,
            cls.SEQUENCE_LEN,
            cls.LINEAGE_SUPERKINGDOM,
        }
    
    @classmethod
    def metadata_fields(cls) -> set[Field]:
        """ Return a list of all metadata table fields for the database."""
        return {
            cls.UNIPROT_ID,
            cls.ORGANISM,
            cls.ORGANISM_ID,
            cls.CATEGORY_ID,
            cls.SEQUENCE,
            cls.SEQUENCE_LEN,
            cls.PROTEIN_IDS,
            cls.PROTEOME_IDS,
            cls.GENES,
            cls.GENOME_IDS,
            cls.LINEAGE,
            cls.LINEAGE_SUPERKINGDOM
        }
    
    @classmethod
    def optional_fields(cls) -> set[Field]:
        """ Returns all fields with an optional FieldType. """
        optional_types = FieldType.optional_types()
        return {field for field in cls if not field is cls.ANY and field.type in FieldType.optional_types()}
    
    @classmethod
    def required_fields(cls) -> set[Field]:
        """ Returns all fields with a required FieldType. """
        return {field for field in cls if not field is cls.ANY and field.type in FieldType.required_types()}

    @property
    def db_name(self) -> str:
        """ Returns the name of the field in the database. """
        return self.name.lower()

    @property
    def search_name(self) -> str:
        """ Returns the name of the field for a search form. """
        return self.value
        
    def __repr__(self) -> str:
        return self.value
    
    def __str__(self) -> str:
        return self.name.lower().replace("_", " ").replace("id", "ID").capitalize()
    
    @property 
    def type(self) -> FieldType:
        """ Returns the FieldType of the corresponding field in a database. """
        if self is self.UNIPROT_ID:
            return FieldType.PRIMARY_TEXT
        elif self is self.SEQUENCE_LEN:
            return FieldType.INTEGER
        elif self in [self.ORGANISM, self.CATEGORY, self.SEQUENCE, self.LINEAGE]:
            return FieldType.TEXT
        elif self is self.LINEAGE_SUPERKINGDOM:
            return FieldType.TEXT_OPTIONAL
        elif self is self.CATEGORY_ID:
            return FieldType.INT_ID
        elif self is self.ORGANISM_ID:
            return FieldType.TEXT_ID
        elif self in [self.PROTEIN_IDS, self.GENOME_IDS]:
            return FieldType.IDS
        elif self in [self.PROTEOME_IDS, self.GENES]:
            return FieldType.IDS_OPTIONAL
        else:
            raise NotImplementedError(f"Not implemented for FieldType {self}.")
        
    @property
    def comparison_type(self) -> ComparisonType:
        """ Returns the ComparisonType to be used in SQL queries for the field. """
        # First treat the sliders as special cases.
        if self is self.SEQUENCE_LEN:
            return ComparisonType.BETWEEN
        # Then all other facets and IDs are assumed to require equal comparison.
        elif self in self.facet_fields() or self.type in [FieldType.PRIMARY_INTEGER, FieldType.PRIMARY_TEXT, FieldType.INT_ID, FieldType.TEXT_ID]:
            return ComparisonType.EQUAL
        # All leftover search terms function through a LIKE comparison.
        elif self in self.search_fields():
            return ComparisonType.LIKE
        # Raise an error for other field types for the sake of exhaustiveness.
        else:
            raise NotImplementedError(f"Not implemented for FieldType {self}.")
    
    def value_from_json(self, json_data: any) -> any:
        if self is self.ORGANISM:
            return json_data["uniprot"]["organism"]["scientificName"]
        elif self is self.ORGANISM_ID:
            return json_data["uniprot"]["organism"]["taxonId"]
        elif self is self.SEQUENCE:
            return json_data["uniprot"]["sequence"]["value"]
        elif self is self.SEQUENCE_LEN:
            return json_data["uniprot"]["sequence"]["length"]
        elif self is self.CATEGORY:
            return json_data["histoneDB"]["category"]
        elif self is self.LINEAGE:
            return json.dumps([lineage["scientificName"] for lineage in json_data["uniprot"]["lineages"]])
        elif self is self.LINEAGE_SUPERKINGDOM:
            superkingdoms = [lineage["scientificName"] for lineage in json_data["uniprot"]["lineages"] if lineage["rank"] == "superkingdom"]
            if superkingdoms:
                if len(superkingdoms) > 1:
                    raise ValueError("Supplied json data has multiple superkingdoms within one lineage")
                
                return superkingdoms[0]
            else:
                return None
        elif self is self.PROTEIN_IDS:
            ref_properties = [ref["properties"] for ref in json_data["uniprot"]["uniProtKBCrossReferences"]]
            pids = [property["value"] for ref in ref_properties for property in ref if property["key"] == "ProteinId"]
            if pids:
                return json.dumps(pids)
            else:
                return None
        elif self is Field.PROTEOME_IDS:
            pmids = [ref["id"] for ref in json_data["uniprot"]["uniProtKBCrossReferences"] if ref["database"] == "Proteomes"]
            if pmids:
                return json.dumps(pmids)
            else:
                return None
        elif self is Field.GENES:
            if not "genes" in json_data["uniprot"].keys():
                return None

            for gen in json_data["uniprot"]["genes"]:
                if "geneName" in gen.keys():
                    gids = [gen["geneName"]["value"]]
                elif "orfNames" in gen.keys():
                    gids = [orf_name["value"] for orf_name in gen["orfNames"]]
                else:
                    return None
            
            return json.dumps(gids)
        elif self is self.GENOME_IDS:
            gmids = [ref["id"] for ref in json_data["uniprot"]["uniProtKBCrossReferences"] if ref["database"] == "EMBL"]
            if gmids:
                return json.dumps(gmids)
            else:
                return None
        else:
            raise NotImplementedError(f"Not implemented for FieldType {self}.")
    
#***===== ResultCounts Class =====***#
@dataclass(eq=False, frozen=True)
class ResultCounts:
    total: int
    categories: Counter[Sequence[str]]
    superkingdoms: Counter[Sequence[str]]
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

        cat_idx = columns.index("category")
        categories = Counter([res[cat_idx] for res in results])

        lin_idx = columns.index("lineage_json")
        superkingdoms = Counter([find_superkingdom(res[lin_idx]) for res in results])

        if len(results) == 0:
            max_seq_len = 0
        else:
            seq_len_idx = columns.index("sequence_len")
            max_seq_len = max([res[seq_len_idx] for res in results])
        
        object.__setattr__(self, "total", len(results))
        object.__setattr__(self, "categories", categories)
        object.__setattr__(self, "superkingdoms", superkingdoms)
        object.__setattr__(self, "max_seq_len", max_seq_len)

#***===== Create Blueprint =====***#
bp  = flask.Blueprint("types", __name__)

#***===== Register Template Filters =====***#
@bp.app_template_filter("field_name")
def field_name(s: str) -> str:  
    return str(Field(s))

#***===== Register Jinja Context Processors =====***#
@bp.app_context_processor
def inject_field():
    return {"Field": Field}