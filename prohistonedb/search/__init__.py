""" The endpoint for all search requests. """
#***===== Imports =====***#
#*----- Standard Library -----*#
from typing import Sequence, Mapping
from pathlib import Path
import json

#*----- Flask & Flask Extensions -----*#
import flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#
from ..database import models
from ..categories import get_categories

#***===== Functions =====***#
# TODO: Automatic column names
def results_to_histones(results: Sequence[Mapping]) -> list[models.Histone]:
    histones = []

    for result in results:
        categories = get_categories()

        lineage_json = json.loads(result["lineage_json"])
        lineage = []
        for item in lineage_json:
            lineage.append(models.Lineage(item["taxonId"], item["scientificName"], item["rank"], item["hidden"]))

        lineage.reverse()

        if result["proteome_ids"] is None:
            proteome_ids = None
        else:
            proteome_ids = json.loads(result["proteome_ids"])
        
        if result["genes"] is None:
            genes = None
        else:
            genes = json.loads(result["genes"])
        
        ranks = json.loads(result["ranks"])

        histones.append(models.Histone(
            uniprot_id=result["uniprot_id"],
            organism=models.Organism(result["organism_id"], result["organism"]),
            sequence=models.Sequence(result["sequence"]),
            category=categories[result["category_id"]],
            lineage=lineage,
            protein_ids=json.loads(result["protein_ids"]),
            proteome_ids=proteome_ids,
            genes=genes,
            genome_ids=json.loads(result["genome_ids"]),
            multimer_rankings={models.Multimer(multimer):ranks[multimer] for multimer in ranks.keys()},
            rel_path=Path(result["rel_path"]),
        ))
    
    return histones

#***===== Create Blueprint =====***#
bp  = flask.Blueprint("search", __name__, url_prefix="/search")

#***===== Import Sub-Modules =====***#
from . import routes
