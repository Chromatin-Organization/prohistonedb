""" The routes for the session endpoint. """
#***===== Imports =====***#
#*----- Standard library -----*#
from typing import Optional

#*----- Flask & Flask Extenstions -----*#
import flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#
from .types import CartItem

from ..types import Field
from ..database import get_db
from ..search import sql

#***===== Blueprint Import =====***#
from . import bp

#***===== Utility Functions =====*#
def init_cart():
    if not isinstance(flask.session.get("basket"), list):
        flask.session.setdefault("basket", [])

#***===== Route Definitions =====***#
@bp.route("/cart", methods = ["GET", "DELETE"])
def cart():
    """
    Handles HTTP requests for the download cart as a whole.
    Possible HTTP requests:
        - GET: Returns the full list of histones in the download cart.
        - DELETE: Clear the download cart of all histones. Returns a 204 when successful.
    """
    # Make sure the download cart exists
    init_cart()

    # Handle the different types of requests
    if flask.request.method == "GET":
        # For GET requests, return the download cart.
        filters = [sql.Filter(Field.UNIPROT_ID, uid) for uid in flask.session["basket"]]
        
        if len(filters) <= 0:
            return [], 200
        elif len(filters) == 1:
            filter = filters[0]
        else:
            filter = sql.OrFilter(filters)

        query = sql.Query(filter=filter)
        db = get_db()
        results = query.execute(db).fetchall()

        items = [CartItem(uniprot_id=result[Field.UNIPROT_ID.db_name], organism_name=result[Field.ORGANISM.db_name]) for result in results]
        return items, 200
    elif flask.request.method == "DELETE":
        # For DELETE requests, clear the download cart and return a 204.
        flask.session["basket"] = []
        flask.session.modified = True
        return '', 204
    else:
        # For invalid request types, return 405.
        flask.current_app.logger.debug(f"Unimplemented request type {flask.request.method}")
        return '', 405

@bp.route("/cart/item/<uniprot_id>", methods=["POST", "DELETE"])
@bp.route("/cart/items", methods = ["POST", "DELETE"])
def cart_items(uniprot_id: Optional[str] = None):
    """ 
    Handles HTTP requests related to individual items for the download cart.
    Possible HTTP requests:
        - POST: Add the uids to the download cart. Ignores uids that are not in the database.
        - DELETE: Remove the uids from the download cart. Ignores uids not in the cart.
    """
    # Make sure the download cart exists
    init_cart()

    # Pre-process the Uniprot ID inputs.
    if uniprot_id is None:
        uids = flask.request.json

        if not uids:
            flask.current_app.logger.debug("Session cookie request failed. No Uniprot IDs where supplied.")
            return '', 404
        elif not isinstance(uids, list):
            uids = [uids]
    else:
        uids = [uniprot_id]
    
    # Handle the different types of requests.
    if flask.request.method == "POST":
        # For POST requests, add the uids to the cart.
        for uid in uids:
            if uid in flask.session["basket"]:
                continue

            filter = sql.Filter(Field.UNIPROT_ID, uid)
            query = sql.Query(filter=filter)

            db = get_db()
            if query.execute(db).fetchone():
                flask.session["basket"].append(uid)

        flask.session.modified = True
        return '', 204
    elif flask.request.method == "DELETE":
        # For DELETE requests, remove the uids from the cart.
        for uid in uids:
            try:
                flask.session["basket"].remove(uid)
            except:
                flask.current_app.logger.debug(f"Could not remove {uid} from download cart. Skipping...")
                pass

        flask.session.modified = True
        return '', 204
    else:
        # For invalid request types, return 405.
        flask.current_app.logger.debug(f"Unimplemented request type {flask.request.method}")
        return '', 405