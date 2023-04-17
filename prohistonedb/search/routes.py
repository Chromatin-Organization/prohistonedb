""" The routes for the search results endpoint. """
#***===== Imports =====***#
#*----- Standard library -----*#

#*----- Flask & Flask Extenstions -----*#
import flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#
from .sql import Filter, OrFilter, build_sql
from . import sql

#***===== Blueprint Import =====***#
from . import bp

#***===== Route Definitions =====***#
@bp.route("", methods=["GET"])
def index():
    """ Process the search request and render the search results. """
    #TODO: Add Input Validation. (currently just discards non standard keys)
    #TODO: Handle current filter=[field]&q=[value] method for search submission.
    #TODO: Change filters based on field types.
    #TODO: Modify templates to correspond with expected query parameters.
    
    args = flask.request.args
    accepted_fields = [field.value for field in sql.FieldType]
    filters = [sql.Filter(field, value) for field, value in args.items() if field in accepted_fields]
    sql_str = sql.build_sql("test", sql.OrFilter(filters))
    print(sql_str)

    return flask.render_template('pages/search.html.j2')