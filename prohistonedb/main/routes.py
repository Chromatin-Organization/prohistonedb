""" The routes for the main endpoint. """
#***===== Imports =====***#
#*----- Standard library -----*#
from typing import Optional
from zipfile import ZipFile
from tempfile import TemporaryFile
from io import BytesIO
import urllib
import time

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

@bp.route("/changelog", methods=["GET"])
def changelog():
    """ Render the changelog page. """
    return flask.render_template("pages/changelog.html.j2")

@bp.route("/download", methods=["GET"])
def download():
    """ Supply a downloadable zip file for the requested histones. """
    # Retrieve the Uniprot IDs for the histones that need to be downloaded.
    uids = flask.request.args.getlist(Field.UNIPROT_ID.search_name)
    
    # Deal with edge cases
    if len(uids) == 0:
        return '', 204
    
    if len(uids) == 1:
        return flask.redirect(f"https://prohistonedb.universiteitleiden.nl/data/zips/{uids[0]}.zip")
    
    # Generate a zip file
    tmp = TemporaryFile()

    flask.current_app.logger.debug(f"Generating temporary file for download: {tmp.name}")

    with ZipFile(tmp, "w") as zf:
        for uid in uids:
            response = urllib.request.urlopen(f"https://prohistonedb.universiteitleiden.nl/data/zips/{uid}.zip")
            zip = ZipFile(BytesIO(response.read()), "r")

            for name in zip.namelist():
                zf.writestr(name, zip.open(name).read())
        
    tmp.seek(0)

    name = f"prohistonedb_bulk_{time.strftime('%Y%m%d%H%M%S')}.zip"
    return flask.send_file(tmp, mimetype="application/zip", as_attachment=True, download_name=name)