""" The routes for the main endpoint. """
#***===== Imports =====***#
#*----- Standard library -----*#
from typing import Optional

from pathlib import Path

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
    db = database.get_db()
    query = sql.SQL(filter = sql.Filter(FieldType.UNIPROT_ID, uniprot_id))
    results = query.execute(db)
    entry = results.fetchone()

    for key in entry.keys():
        print(f'"{key}": {entry[key]}')

    if multimer is None:
        multimer = entry["prefered_multimer"]

    if multimer == "monomer":
        path = str(Path(flask.current_app.instance_path) / Path(entry["rel_path"]))
    else:
        path = str(Path(flask.current_app.instance_path) / Path(entry["rel_path"] + f"_{multimer}"))
        
    return flask.render_template('pages/entry.html.j2', entry = entry, multimer = multimer, path = path)

@bp.route('/about', methods=["GET"])
def about():
    """ Render the about page. """
    return flask.render_template('pages/about.html.j2')