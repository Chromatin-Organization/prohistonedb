""" The endpoint for the categorie pages. """
#***===== Imports =====***#
#*----- Standard Library -----*#

#*----- Flask & Flask Extenstions -----*#
import flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#

#***===== Create Blueprint =====***#
bp  = flask.Blueprint("categories", __name__, url_prefix="/categories")

#***===== Import Sub-Modules =====***#
from . import routes
