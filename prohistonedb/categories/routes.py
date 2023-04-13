""" The routes for the main endpoint. """
#***===== Imports =====***#
#*----- Standard library -----*#

#*----- Flask & Flask Extenstions -----*#
import flask
import jinja2

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#

#***===== Blueprint Import =====***#
from . import bp

#***===== Route Definitions =====***#
@bp.route('/overview')
def overview():
    """ Render an overview page for all the categories. """
    return flask.render_template('pages/categories.html.j2')