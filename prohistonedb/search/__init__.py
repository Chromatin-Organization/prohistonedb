""" The endpoint for all search requests. """
#***===== Imports =====***#
#*----- Standard Library -----*#

#*----- Flask & Flask Extenstions -----*#
import flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#

#***===== Create Blueprint =====***#
bp  = flask.Blueprint("search", __name__, url_prefix="/search")

#***===== Import Sub-Modules =====***#
from . import routes

