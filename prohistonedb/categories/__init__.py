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

#***===== Category class =====***#
@dataclass(frozen=True)
class Category:
    """ A simple dataclass to hold a Category. If no short name is supplied, it will default to the standard name. """
    id: int
    name: str
    preferred_multimer: str
    short_name: Optional[str] = None

    def __post_init__(self):
        if self.short_name is None:
            object.__setattr__(self, "short_name", self.name)

    def __str__(self) -> str:
        return self.name

#***===== Functions =====***#
def get_categories() -> list[Category]:
    """ Returns the categories in the database from the app context. Queries the database if they haven't been set yet. """
    if "categories" not in flask.g:
        sql = "SELECT * FROM categories ORDER BY name"
        db = database.get_db()
        results = db.execute(sql)
        categories = results.fetchall()
        flask.g.categories = [Category(**category) for category in categories]
    
    return flask.g.categories

#***===== Create Blueprint =====***#
bp  = flask.Blueprint("categories", __name__, url_prefix="/categories")

#***===== Import Sub-Modules =====***#
from . import routes

#***===== Register Jinja Context Processors =====***#
@bp.app_context_processor
def inject_categories():
    categories = get_categories()
    print(categories)
    return {"categories": categories}
