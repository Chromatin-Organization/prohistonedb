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
    #TODO: Change filters based on field types.
    #TODO: Modify templates to correspond with expected query parameters.
    
    # Prepare some variables
    args = flask.request.args.copy()
    accepted_fields = [field.value for field in sql.FieldType]

    # Convert filter=[field]&q=[value] syntax to [filter]=[value] pairs in de MultiDict
    fields = args.keys()
    if "filter" in fields:
        if not "q" in fields:
            raise ValueError('Search bar should return fields in "filter" together with values in "q".')
        
        fields = args.poplist("filter")
        values = args.poplist("q")

        if len(fields) != len(values):
            raise ValueError('"filter" and "q" should have the same number of items.')
        
        map(lambda _f, _v: args.add(_f, _v), zip(fields, values))      

    # Create a combined filter from all the search conditions and generate the SQL code to search the database. 
    filters = [sql.Filter(field, value) for field, value in args.items() if field in accepted_fields]
    sql_str = sql.build_sql("test", sql.OrFilter(filters))
    print(sql_str)

    return flask.render_template('pages/search.html.j2')