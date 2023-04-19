""" The routes for the main endpoint. """
#***===== Imports =====***#
#*----- Standard library -----*#

#*----- Flask & Flask Extenstions -----*#
import flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#

#***===== Blueprint Import =====***#
from . import bp

#***===== Route Definitions =====***#
@bp.route("/", methods=["GET"])
def index():
    """ Render the index page. """
    return flask.render_template('pages/index.html.j2')

#TODO: Different entry pages for different multimers.
@bp.route("/entry/<uniprotID>", methods=["GET"])
def entry(uniprotID: str):
    """ Render the structure page for a specified entry. """
    return flask.render_template('pages/entry.html.j2', uniprotID = uniprotID)

@bp.route('/about', methods=["GET"])
def about():
    """ Render the about page. """
    return flask.render_template('pages/about.html.j2')