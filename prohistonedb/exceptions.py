""" A module defining custom types and pages for exception handling. """
#***===== Imports =====***#
#*----- Standard Library -----*#
from typing import Union

#*----- Flask & Flask Extenstions -----*#
import flask
from flask import Flask

#*----- Other External packages -----*#
from werkzeug.exceptions import HTTPException

#*----- Custom packages -----*#

#*----- Local imports -----*#

#***===== Flask App Initialization =====***#
def register_handlers(app: Flask):
    app.register_error_handler(403, error_page)
    app.register_error_handler(404, error_page)
    app.register_error_handler(500, error_page)

#***===== HTTP Error Handlers =====***#
def error_page(e: Union[Exception, int]):
    if isinstance(e, HTTPException):
        return flask.render_template("pages/error.html.j2", status=e.code), e.code
    else:
        flask.current_app.logger.error(f"Unknown error!: {e}")
        return flask.render_template("pages/error.html.j2"), 500