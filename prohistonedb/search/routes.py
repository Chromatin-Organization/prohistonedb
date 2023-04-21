""" The routes for the search results endpoint. """
#***===== Imports =====***#
#*----- Standard library -----*#

#*----- Flask & Flask Extenstions -----*#
import flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#
from . import sql
from ..database.types import FieldType
from .. import database

#***===== Blueprint Import =====***#
from . import bp

#***===== Route Definitions =====***#
@bp.route("", methods=["GET"])
def index():
    """ Process the search request and render the search results. """
    #TODO: Add Input Validation. (currently just discards non standard keys)
    # Prepare some variables
    NUM_RESULTS = 20
    args = flask.request.args.copy()
    fields = args.keys()

    accepted_fields = FieldType.accepted_fields()
    accepted_fields.append("any")

    # Convert filter=[field]&q=[value] syntax to [filter]=[value] pairs in de MultiDict
    if "filter" in fields:
        if "q" in fields:
            flask.current_app.logger.debug("Found 'filter=[field]&q=[value]' syntax. Converting to '[field]=[value]' syntax...")
            fields = args.poplist("filter")
            values = args.poplist("q")

            if len(fields) == len(values):
                for field, value in zip(fields, values):
                    args.add(field, value)
            else:
                flask.current_app.logger.error('"filter" and "q" should have the same number of items.')
        else:
            flask.current_app.logger.error("Search bar should return fields in 'filter' together with values in 'q'.")

    # Create filters for all the search field.
    filters = []
    fields = args.keys()
    flask.current_app.logger.debug(f"Valid fields: {accepted_fields}")
    flask.current_app.logger.debug(f"Request fields (after conversion): {fields}")

    for field in fields:
        #! Ignore none supported fields for now. Change in future!
        if not field in accepted_fields:
            flask.current_app.logger.debug(f"Ignoring '{field}' since it is not a valid filter.")
            continue

        # Create a logical OR filter per field
        values = args.getlist(field)

        if field == "any":
            filters.append(sql.OrFilter([sql.AnyFilter(value) for value in values]))
        else:
            filters.append(sql.OrFilter([sql.Filter(field, value) for value in values]))

    # Create a logical AND filter that combines the filters per field and generate SQL code for a database Query from it.
    filter = sql.AndFilter(filters)
    flask.current_app.logger.debug(f"Generated filters: {filters}")

    query = sql.SQL("search", filter=filter)
    flask.current_app.logger.debug(f"Generated SQL query: {str(query)}")

    # Get the database connection and query the generated SQL code.
    conn = database.get_db()
    results = query.execute(conn)
    results = results.fetchmany(NUM_RESULTS)
    flask.current_app.logger.debug(f"Displaying first {NUM_RESULTS} results")
    return flask.render_template('pages/search.html.j2', results=results)