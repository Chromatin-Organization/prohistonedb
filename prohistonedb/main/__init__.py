""" The endpoint for all root pages. """
#***===== Imports =====***#
#*----- Standard Library -----*#

#*----- Flask & Flask Extenstions -----*#
import flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#

#***===== Create Blueprint =====***#
bp  = flask.Blueprint("main", __name__)

#***===== Import Sub-Modules =====***#
from . import routes

