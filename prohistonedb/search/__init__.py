""" The endpoint for all search requests. """
#***===== Imports =====***#
#*----- Standard Library -----*#
from typing import Sequence, Mapping
from pathlib import Path
import json
import datetime

#*----- Flask & Flask Extensions -----*#
import flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#
from ..types import Field
from ..database import models, get_categories

#***===== Functions =====***#
def results_to_histones(results: Sequence[Mapping]) -> list[models.Histone]:
    histones = []

    for result in results:
        categories = get_categories()

        lineage_json = json.loads(result[Field.LINEAGE.db_name+"_json"])
        lineage = []
        for item in lineage_json:
            lineage.append(models.Lineage(item["taxonId"], item["scientificName"], item["rank"], item["hidden"]))

        lineage.reverse()

        if result[Field.PROTEOME_IDS.db_name] is None:
            proteome_ids = None
        else:
            proteome_ids = json.loads(result[Field.PROTEOME_IDS.db_name])
        
        ranks = json.loads(result["ranks"])

        histones.append(models.Histone(
            uniprot_id=result[Field.UNIPROT_ID.db_name],
            organism=models.Organism(result[Field.ORGANISM_ID.db_name], result[Field.ORGANISM.db_name]),
            sequence=models.Sequence(result[Field.SEQUENCE.db_name]),
            category=categories[result[Field.CATEGORY_ID.db_name]],
            lineage=lineage,
            protein_ids=json.loads(result[Field.PROTEIN_IDS.db_name]),
            proteome_ids=proteome_ids,
            gene_names=json.loads(result[Field.GENE_NAMES.db_name]),
            genome_ids=json.loads(result[Field.GENOME_IDS.db_name]),
            pdb_ids=json.loads(result["pdb_ids"]),
            multimer_rankings={models.Multimer(multimer):ranks[multimer] for multimer in ranks.keys()},
            publications=json.loads(result["publications"]),
            rel_path=Path(result["rel_path"]),
            last_updated=datetime.datetime.strptime(result["last_updated"], "%Y-%m-%d %H:%M:%S")
        ))
    
    return histones

#***===== Create Blueprint =====***#
bp  = flask.Blueprint("search", __name__, url_prefix="/search")

#***===== Import Sub-Modules =====***#
from . import routes
