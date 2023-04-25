""" The routes for the main endpoint. """
#***===== Imports =====***#
#*----- Standard library -----*#
from typing import Optional

import json

#*----- Flask & Flask Extenstions -----*#
import flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#
from ..search import sql
from .. import database
from ..database.types import FieldType

#***===== Blueprint Import =====***#
from . import bp

#***===== Route Definitions =====***#
@bp.route("/", methods=["GET"])
def index():
    """ Render the index page. """
    return flask.render_template('pages/index.html.j2')

#TODO: Input sanitization for multimer str.
@bp.route("/entry/<uniprot_id>", methods=["GET"])
@bp.route("/entry/<uniprot_id>/<multimer>", methods=["GET"])
def entry(uniprot_id: str, multimer: Optional[str] = None):
    """ Render the structure page for a specified entry. """
    JSON_FIELDS = ["lineage", "lineage_json", "protein_id", "proteome_id", "gen_id", "genome_id", "ranks"]

    db = database.get_db()
    query = sql.SQL(filter = sql.Filter(FieldType.UNIPROT_ID, uniprot_id))
    results = query.execute(db)
    result = results.fetchone()
    entry = {}

    for key in result.keys():
        if key in JSON_FIELDS:
            entry[key] = json.loads(result[key])
        else:
            entry[key] = result[key]

    entry["multimers"] = [multimer for multimer in entry["ranks"].keys() if entry["ranks"][multimer] != None]
    print(entry)

    if multimer is None:
        multimer = entry["prefered_multimer"]

    path = "data/" + entry["rel_path"] + "/" + entry["uniprot_id"]

    if multimer != "monomer":
        path = path + f"_{multimer}"
        
    return flask.render_template('pages/entry.html.j2', entry = entry, multimer = multimer, path = path)

@bp.route('/about', methods=["GET"])
def about():
    """ Render the about page. """
    return flask.render_template('pages/about.html.j2')