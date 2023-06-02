""" The routes for the main endpoint. """
#***===== Imports =====***#
#*----- Standard library -----*#
from typing import Optional

#*----- Flask & Flask Extenstions -----*#
import flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#
from ..types import FieldType

from .. import database
from ..database import models

from ..search import sql, results_to_histones

#***===== Blueprint Import =====***#
from . import bp

#***===== Route Definitions =====***#
@bp.route("/", methods=["GET"])
def index():
    """ Render the index page. """
    return flask.render_template('pages/index.html.j2')

@bp.route("/entry/<uniprot_id>", methods=["GET"])
@bp.route("/entry/<uniprot_id>/<multimer>", methods=["GET"])
def entry(uniprot_id: str, multimer: Optional[str] = None):
    """ Render the structure page for a specified entry. """
    JSON_FIELDS = ["lineage", "lineage_json", "protein_id", "proteome_id", "gen_id", "genome_id", "ranks"]

    args = flask.request.args
    if not "rank" in args:
        rank = 1
    else:
        rank = int(args["rank"])

    if rank < 1 or rank > 6:
        raise ValueError(f"'{rank}' is not a valid value for the model rank.")
    
    flask.current_app.logger.debug(f"Currently selected rank: {rank}")

    db = database.get_db()
    query = sql.Query(filter = sql.Filter(FieldType.UNIPROT_ID, uniprot_id))
    results = query.execute(db)
    result = results.fetchone()

    entry = results_to_histones([result])[0]
    flask.current_app.logger.debug(f"Histone entry: {entry}")

    # * Currently falls back to the preferred multimer for ANY invalid input.
    # ? Should we keep it like this or should we add more conditions for input validation?
    try:
        multimer = models.Multimer(multimer)
    except:
        flask.current_app.logger.debug(f"{multimer} is an invalid input for 'multimer'. Falling back to default.")
        multimer = entry.category.preferred_multimer
    
    # TODO: Better error handling
    if not entry.has_multimer(multimer):
        raise ValueError(f"Multimer '{multimer}' is not available for {uniprot_id}")   
        
    return flask.render_template('pages/entry.html.j2', entry = entry, multimer = multimer, rank = rank)

@bp.route('/about', methods=["GET"])
def about():
    """ Render the about page. """
    return flask.render_template('pages/about.html.j2')