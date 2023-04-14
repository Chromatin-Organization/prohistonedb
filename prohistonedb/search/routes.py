""" The routes for the search results endpoint. """
#***===== Imports =====***#
#*----- Standard library -----*#

#*----- Flask & Flask Extenstions -----*#
import flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#
from .sql import Filter, OrFilter, build_sql

#***===== Blueprint Import =====***#
from . import bp

#***===== Route Definitions =====***#
@bp.route("", methods=["GET"])
def index():
    """ Process the search request and render the search results. """
    #TODO: Add Input Validation.
    #TODO: Change filters based on field types.
    #TODO: Modify templates to correspond with expected query parameters.
    #TODO: Implement actual search functionality.
    
    args = flask.request.args
    filters = [Filter(field, value) for field, value in args.items()]
    sql = build_sql("test", OrFilter(filters))
    print(sql)

    return flask.render_template('pages/search.html.j2')