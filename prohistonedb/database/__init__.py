""" A blueprint for mapping to the database package. """
#***===== Imports =====***#
#*----- Standard Library -----*#
from pathlib import Path
import json

#*----- Flask & Flask Extenstions -----*#
import flask
from flask import Flask

#*----- Other External packages -----*#
import click

#*----- Custom packages -----*#

#*----- Local imports -----*#
from . import connections
from .models import Multimer, Category

from ..types import Field, FieldType

#***===== Initialization & Teardown =====***#
def init_app(app: Flask):
    """ Register the database teardown and CLI commands onto the Flask app. """
    app.teardown_appcontext(teardown_db)
    app.register_blueprint(bp)

def get_db() -> connections.DatabaseConnection:
    """ Retrieve the Database connection from the app context. Also establishes the connection if necessary. """
    if "db" not in flask.g:
        flask.g.db = connections.SQLiteConnection(flask.current_app.config["DATABASE"])
        flask.g.db.connect()
    
    return flask.g.db

def teardown_db(exception: Exception):
    """ Close down the database connection stored in the application context. """
    db = flask.g.pop("db", None)

    if db is not None:
        db.close()

#***===== Request level functions =====***#
def get_categories() -> dict[int, Category]:
    """ Returns the categories in the database from the app context. Queries the database if they haven't been set yet. """
    if "categories" not in flask.g:
        sql = "SELECT * FROM categories ORDER BY name"
        db = get_db()
        results = db.execute(sql)
        categories = results.fetchall()
        flask.g.categories = {category["id"]:Category(**category) for category in categories}
    
    return flask.g.categories

#***===== Database Set-Up Functions =====***#
def init_db():
    """ Creates a database with empty tables and corresponding indexes. """ 
    # Create the database
    conn = get_db()

    # Create the categories table
    flask.current_app.logger.info(f"Creating the categories table.")
    multimer_options =  "', '".join([multimer.value for multimer in Multimer])
    conn.execute(f"""
        CREATE TABLE categories (
            id {conn.sql_field_type(FieldType.PRIMARY_INTEGER)},
            name {conn.sql_field_type(FieldType.TEXT)},
            preferred_multimer {conn.sql_field_type(FieldType.TEXT_OPTIONAL)} CHECK( preferred_multimer IN ('{multimer_options}') ),
            short_name {conn.sql_field_type(FieldType.TEXT_OPTIONAL)},
            has_page {conn.sql_field_type(FieldType.INTEGER)} CHECK( has_page IN (0, 1) )
        )
    """)

    # Add indexes for the categories table
    conn.execute("CREATE INDEX idx_name ON categories(name)")

    # Create the metadata table
    flask.current_app.logger.info(f"Creating the metadata table.")

    sql = "CREATE TABLE metadata (\n"
    for field in Field.metadata_fields():
        sql += f"    {field.db_name} {conn.sql_field_type(field.type)},\n"
    
    sql += f"    rel_path {conn.sql_field_type(FieldType.TEXT)},\n"
    sql += f"    ranks {conn.sql_field_type(FieldType.TEXT_OPTIONAL)},\n"
    sql += f"    {field.LINEAGE.db_name}_json {conn.sql_field_type(FieldType.TEXT)},"
    sql += f"    FOREIGN KEY ({Field.CATEGORY_ID.db_name}) REFERENCES categories(id)\n"
    sql += ")"
    conn.execute(sql)

    # Add indexes for the metadata table
    flask.current_app.logger.info(f"Creating indexes for the metadata table.")
    for field in Field.metadata_fields() & Field.search_fields():
        conn.execute(f"CREATE INDEX idx_{field.db_name} ON metadata({field.db_name})")

    # Create a view for accessing the necessary data in a search
    conn.execute(f"""
        CREATE VIEW search AS
            SELECT metadata.*, categories.name AS {Field.CATEGORY.db_name}, categories.preferred_multimer
            FROM metadata
            LEFT JOIN categories ON metadata.{Field.CATEGORY_ID.db_name} = categories.id
    """)

    # Commit the changes to the database
    conn.commit()

def update_db_categories():
    """ Update the database with the data in the categories JSON file. """
    # Get a database connection
    conn = get_db()

    # Make sure that the categories JSON file exists
    categories_json = Path(flask.current_app.config["CATEGORIES_JSON"])

    if not categories_json.is_file():
        raise Exception("Config option 'CATEGORIES_JSON' does not point to a file.")

    # Open the categories JSON file and load the data
    with open(categories_json, 'r') as f:
        categories_json = json.load(f)

        # Load all the categories data into a list
        categories = []

        for category in categories_json:
            category_json = categories_json[category]

            data = {}
            data["name"] = category
            data["preferred_multimer"] = category_json["preferredMultimer"]
            if "shortName" in category_json:
                data["short_name"] = category_json["shortName"]
            else:
                data["short_name"] = None
            if "has_page" in categories_json:
                data["has_page"] = int(categories_json["has_page"])
            else:
                data["has_page"] = int(False)

            categories.append(data)

        # Execute the SQL query on the database
        sql = "INSERT OR REPLACE INTO categories (name, preferred_multimer, short_name, has_page) VALUES (:name, :preferred_multimer, :short_name, :has_page)"
        conn.executemany(sql, categories)
        conn.commit()

def update_db_metadata():
    """ Update the database with the data in the metadata JSON file.  """
    # Get a database connection
    conn = get_db()

    # Set-up some useful variables
    search_fields = ((Field.search_fields() | Field.facet_fields()) & Field.metadata_fields()) - {Field.CATEGORY_ID}

    # Make sure that the metadata JSON file exists
    metadata_json = Path(flask.current_app.config["METADATA_JSON"])

    if not metadata_json.is_file():
        raise Exception("Config option 'METADATA_JSON' does not point to a file.")
    
    # Open the metadata JSON file and load the data
    with open(metadata_json, 'r') as f:
        metadata_json = json.load(f)

        # Load all the metadata into a list
        metadata = []

        for uid in metadata_json:
            data = {}
            data[Field.UNIPROT_ID.db_name] = uid
            uid_json = metadata_json[uid]

            # Add the searchable fields
            data = {field.db_name:field.value_from_json(uid_json) for field in (search_fields | {Field.CATEGORY})- {Field.UNIPROT_ID}}
            data[Field.UNIPROT_ID.db_name] = uid
            
            # Add additional information
            multimers_json = uid_json["histoneDB"]["multimer"]
            ranks = {}

            for multimer in multimers_json:
                # skip any non-valid multimers
                try:
                    Multimer(multimer)
                except:
                    flask.current_app.logger.warning(f"Entry {uid}: Unknown multimer '{multimer}' found. Skipping...")
                    continue

                if not multimers_json[multimer]:
                    # * Removed debugging since it was overly verbose
                    # flask.current_app.logger.debug(f"Entry {uid} has no structure for '{multimer}'. Skipping...")
                    continue
                
                ranks_json = uid_json["histoneDB"]["rankModel"][multimer]
                ranks[multimer] = [int(ranks_json["rank_" + str(n)].replace("model_", "")) for n in range(1, 6)]
            
            data["ranks"] = json.dumps(ranks)
            data["rel_path"] = uid_json["histoneDB"]["relPath"]
            data[Field.LINEAGE.db_name+"_json"] = json.dumps(uid_json["uniprot"]["lineages"])

            # Apply all the fields for this uid
            metadata.append(data)

        # Execute the SQL query on the database
        fields = {field.db_name for field in search_fields}
        fields = fields | {Field.LINEAGE.db_name+"_json", "rel_path", "ranks"} - {Field.CATEGORY_ID.db_name}

        sql = "INSERT INTO metadata (\n    "
        sql += ",\n    ".join(fields)
        sql += f",\n    {Field.CATEGORY_ID.db_name}\n)\n"
        sql += "SELECT\n    :"
        sql += ",\n    :".join(fields)
        sql += f",\n    categories.id\n"
        sql += "FROM categories\n"
        sql += f"WHERE name = :{Field.CATEGORY.db_name}"

        conn.executemany(sql, metadata)
        conn.commit()

def delete_db():
    db_path = Path(flask.current_app.config["DATABASE"])
    db_path.unlink(missing_ok=True)

#***===== Create Blueprint =====***#
bp  = flask.Blueprint("database", __name__, cli_group="database")

#***===== Register Jinja Context Processors =====***#
@bp.app_context_processor
def inject_categories():
    categories = get_categories()
    flask.current_app.logger.debug(f"Categories present in the database: {[(id, category.name) for (id, category) in categories.items()]}")
    return {"categories": categories}

@bp.app_context_processor
def inject_max_sequence_length():
    db = get_db()
    max_seq_len = db.execute(f"SELECT MAX({Field.SEQUENCE_LEN.db_name}) FROM search").fetchone()[0]
    if not max_seq_len:
        max_seq_len = 0
    flask.current_app.logger.debug(f"The maximum sequence lengths found in the database is {max_seq_len}.")
    return {"max_seq_len": max_seq_len}

#***===== Register CLI commands =====***#
@bp.cli.command("create")
@click.option('-f', '--force', is_flag=True, help="Enables rewriting of the existing database file.")
def create(force: bool = False):
    """ Create a new database from the 'categories' and 'metadata' JSON files. """
    if force:
        # If overwriting is forced, delete the current database.
        delete_db()
    else:
        # Otherwise, make sure the database file does not exist yet.
        db_path = Path(flask.current_app.config["DATABASE"])

        if db_path.is_file():
            raise Exception("A database file already exists. If you want to update it, use 'flask database update' instead.")

    # Create an empty database.
    init_db()

    # Fill the categories table from the categories json file.
    update_db_categories()

    # Fill the metadata table from the metadata json file.
    update_db_metadata()

@bp.cli.command("update")
def update():
    """ 
        Updates the database based on the 'categories' and 'metadata' JSON files.
        WARNING: Existing entries may be overwritten.
    """
    # Update the categories table from the categories json file.
    update_db_categories()

    # Update the metadata table from the metadata json file.
    update_db_metadata()
