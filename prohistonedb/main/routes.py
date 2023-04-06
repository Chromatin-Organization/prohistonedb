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
    return flask.render_template("index.html.j2")

@bp.route("/entry", methods=["GET"])
def entry():
    """ Render the structure page for a specified entry. """
    raise NotImplementedError
