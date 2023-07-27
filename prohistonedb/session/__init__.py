""" The endpoint for managing session cookies. """
#***===== Imports =====***#
#*----- Standard Library -----*#

#*----- Flask & Flask Extenstions -----*#
import flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#

#***===== Create Blueprint =====***#
bp  = flask.Blueprint("session", __name__, url_prefix="/session")

#***===== Import Sub-Modules =====***#
from . import routes
