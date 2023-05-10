""" The endpoint for the categorie pages. """
#***===== Imports =====***#
#*----- Standard Library -----*#
from dataclasses import dataclass

from typing import Optional

#*----- Flask & Flask Extenstions -----*#
import flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#
from .. import database
from ..database.models import Category

#***===== Functions =====***#
def get_categories() -> dict[int, Category]:
    """ Returns the categories in the database from the app context. Queries the database if they haven't been set yet. """
    if "categories" not in flask.g:
        sql = "SELECT * FROM categories ORDER BY name"
        db = database.get_db()
        results = db.execute(sql)
        categories = results.fetchall()
        flask.g.categories = {category["id"]:Category(**category) for category in categories}
    
    return flask.g.categories

#***===== Create Blueprint =====***#
bp  = flask.Blueprint("categories", __name__, url_prefix="/categories")

#***===== Import Sub-Modules =====***#
from . import routes

#***===== Register Jinja Context Processors =====***#
@bp.app_context_processor
def inject_categories():
    categories = get_categories()
    flask.current_app.logger.debug(f"Categories present in the database: {[category.name for category in categories]}")
    return {"categories": categories}
