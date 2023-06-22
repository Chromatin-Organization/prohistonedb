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
@bp.route('/overview', methods=["GET"])
def overview():
    """ Render an overview page for all the categories. """
    return flask.render_template('pages/categories.html.j2')

@bp.route("/<id>", methods=["GET"])
def with_id(id: int):
    """ Render a page for a specific category. """
    return flask.render_template("pages/categories.html.j2", id=id)