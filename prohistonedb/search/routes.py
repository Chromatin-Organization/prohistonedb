""" The routes for the search results endpoint. """
#***===== Imports =====***#
#*----- Standard library -----*#
from typing import Optional, Union
import math

#*----- Flask & Flask Extenstions -----*#
import flask

#*----- External packages -----*#
from werkzeug.datastructures import MultiDict

#*----- Custom packages -----*#

#*----- Local imports -----*#
from . import sql
from .types import FieldType
from .. import database
from . import results_to_histones

#***===== Functions =====***#
def convert_args(args: MultiDict) -> MultiDict:
    """Takes request arguments and returns a MultiDict with filter=[field]&q=[value] syntax converted to [filter]=[value] pairs. """
    accepted_fields = FieldType.accepted_fields()
    accepted_fields.append("any")
    
    fields = args.keys()

    if "filter" in fields:
        if not "q" in fields:
            raise Exception("Search bar should return fields in 'filter' together with values in 'q'.")

        flask.current_app.logger.debug("Found 'filter=[field]&q=[value]' syntax. Converting to '[field]=[value]' syntax...")
        filter_fields = args.poplist("filter")
        values = args.poplist("q")

        if len(filter_fields) == len(values):
            for field, value in zip(filter_fields, values):
                # Ignore none supported fields.
                if not field in accepted_fields:
                    flask.current_app.logger.debug(f"Ignoring '{field}' since it is not a valid filter.")
                    continue

                args.add(field, value)
        else:
            flask.current_app.logger.debug(f'"filter" (length {len(filter_fields)}) and "q" (length {len(values)}) do not have the same number of items.')
    
    return args

#? Do we want to change behaviour away from discarding non-valid fields?
def filter_from_args(args: MultiDict) -> Union[sql.Filter, sql.CombinedFilterABC, None]:
    """ Takes request arguments and returns a Filter to be used for an SQL query. """
    accepted_fields = FieldType.accepted_fields()
    accepted_fields.append("any")

    filters = []
    fields = args.keys()
    flask.current_app.logger.debug(f"Valid fields: {accepted_fields}")
    flask.current_app.logger.debug(f"Request fields (after conversion): {fields}")

    for field in fields:
        # Ignore none supported fields.
        if not field in accepted_fields:
            flask.current_app.logger.debug(f"Ignoring '{field}' since it is not a valid filter.")
            continue

        # Create a logical OR filter per field
        values = args.getlist(field)
            
        if field == "any":
            if len(values) == 1:
                filters.append(sql.AnyFilter(values[0]))
            else:
                filters.append(sql.OrFilter([sql.AnyFilter(value) for value in values]))
        else:
            if len(values) == 1:
                filters.append(sql.Filter(field, values[0]))
            else:
                filters.append(sql.OrFilter([sql.Filter(field, value) for value in values]))

    # Create a logical AND filter that combines the filters per field and generate SQL code for a database Query from it.
    if len(filters) == 0:
        filter = None
    elif len(filters) == 1:
        filter = filters[0]
    else:
        filter = sql.AndFilter(filters)

    flask.current_app.logger.debug(f"Generated filters: {filters}")
    return filter

#***===== Blueprint Import =====***#
from . import bp

#***===== Route Definitions =====***#
@bp.route("", methods=["GET"])
@bp.route("/<page>")
def index(page: Optional[int] = None):
    """ Process the search request and render the search results. """
    # Prepare some variables
    NUM_RESULTS = 20

    if page is None:
        page = 1
    
    page = int(page)

    if page <= 0:
        raise ValueError(f"{page} is not a valid page number.")

    # Pre-process query parameters into a search filter
    args = flask.request.args.copy()

    if args == None:
        filter = None
    else:
        # Convert filter=[field]&q=[value] syntax to [field]=[value] syntax
        try:
            args = convert_args(args)
        except Exception as e:
            flask.current_app.logger.exception(**e)

        # Remove duplicates
        for key in args.keys():
            args.setlist(key, list(set(args.getlist(key))))

        # Create a filter from the query parameters
        filter = filter_from_args(args)

    # Select the necessary fields and generate the SQL query
    query = sql.Query(filter=filter)

    # Get the database connection and query the generated SQL code.
    db = database.get_db()
    results = query.execute(db)
    results = results.fetchall()
    results = results_to_histones(results)

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
    return flask.render_template('pages/search.html.j2', results=results, page=page, max_page=max_page, num_results=total_num_results, req_filters=args)