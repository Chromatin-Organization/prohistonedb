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
    raise NotImplementedError