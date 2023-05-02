""" The routes for the search results endpoint. """
#***===== Imports =====***#
#*----- Standard library -----*#
from typing import Optional

import math

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
@bp.route("/<page>")
def index(page: Optional[int] = None):
    """ Process the search request and render the search results. """
    #? Do we want to change behaviour away from discarding non-valid fields?
    # Prepare some variables
    NUM_RESULTS = 20
    args = flask.request.args.copy()
    fields = args.keys()

    accepted_fields = FieldType.accepted_fields()
    accepted_fields.append("any")

    if page is None:
        page = 1
    
    page = int(page)

    if page <= 0:
        raise ValueError(f"{page} is not a valid page number.")

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
        #? Ignore none supported fields for now. Change in future?
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
    filter = sql.AndFilter(filters)
    flask.current_app.logger.debug(f"Generated filters: {filters}")

    # Select the necessary fields and generate the SQL query
    query = sql.SQL(filter=filter)

    # Get the database connection and query the generated SQL code.
    db = database.get_db()
    results = query.execute(db)
    results = results.fetchall()

    # Manage paging to fetch the correct results
    total_num_results = len(results)
    max_page = max(math.ceil(total_num_results / NUM_RESULTS), 1)
    flask.current_app.logger.debug(f"Total number of results: {total_num_results}.")
    flask.current_app.logger.debug(f"Preparing page {page} out of {max_page}.")

    if page > max_page:
        raise ValueError(f"Can't return page {page}. This request only has {max_page} pages.")
    
    idx_min = (page - 1) * NUM_RESULTS
    idx_max = page * NUM_RESULTS - 1
    results = results[idx_min:(idx_max+1)]
    
    flask.current_app.logger.debug(f"Displaying results {idx_min} till {idx_max} for a total of {len(results)} results.")
    return flask.render_template('pages/search.html.j2', results=results, page=page, max_page=max_page, num_results=total_num_results)