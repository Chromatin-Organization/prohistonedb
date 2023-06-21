""" The routes for the main endpoint. """
#***===== Imports =====***#
#*----- Standard library -----*#
from typing import Optional

#*----- Flask & Flask Extenstions -----*#
import flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#
from ..types import Field

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
    args = flask.request.args
    if not "rank" in args:
        rank = 1
    else:
        rank = int(args["rank"])

    if rank < 1 or rank > 6:
        raise ValueError(f"'{rank}' is not a valid value for the model rank.")
    
    flask.current_app.logger.debug(f"Currently selected rank: {rank}")

    db = database.get_db()
    query = sql.Query(filter = sql.Filter(Field.UNIPROT_ID, uniprot_id))
    results = query.execute(db)
    result = results.fetchone()

    # Raise 404 error if no entries are found.
    if not result or len(result) == 0:
        flask.abort(404)

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
    # (Currently just renders the template without multimer info)
    if not entry.has_multimer(multimer):
        return flask.render_template('pages/entry.html.j2', entry = entry, rank = rank)  
        
    return flask.render_template('pages/entry.html.j2', entry = entry, multimer = multimer, rank = rank)

@bp.route('/about', methods=["GET"])
def about():
    """ Render the about page. """
    return flask.render_template('pages/about.html.j2')