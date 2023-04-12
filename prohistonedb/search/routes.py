""" The routes for the search results endpoint. """
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
@bp.route("", methods=["GET"])
def index():
    """ Process the search request and render the search results. """
    #TODO: Implement actual search functionality.
    #TODO: Add arguments for search query parameters.
    return flask.render_template('pages/search.html.j2')