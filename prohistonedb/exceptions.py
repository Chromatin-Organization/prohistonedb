""" A module defining custom types and pages for exception handling. """
#***===== Imports =====***#
#*----- Standard Library -----*#
from typing import Union

#*----- Flask & Flask Extenstions -----*#
import flask
from flask import Flask

#*----- Other External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#

#***===== Flask App Initialization =====***#
def register_handlers(app: Flask):
    app.register_error_handler(404, page_not_found)

#***===== HTTP Error Handlers =====***#
def page_not_found(e: Union[Exception, int]):
    return flask.render_template("pages/404-not-found.html.j2"), 404