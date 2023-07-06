""" A blueprint for mapping to the database package. """
#***===== Imports =====***#
#*----- Standard Library -----*#
from pathlib import Path
import json
from typing import Union

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
            name {conn.sql_field_type(FieldType.TEXT)} UNIQUE,
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

        if field is Field.LINEAGE:
            sql += f"    {field.LINEAGE.db_name}_json {conn.sql_field_type(FieldType.TEXT)},"
    
    sql += f"    rel_path {conn.sql_field_type(FieldType.TEXT)},\n"
    sql += f"    ranks {conn.sql_field_type(FieldType.TEXT_OPTIONAL)},\n"
    sql += f"    last_updated {conn.sql_field_type(FieldType.TIMESTAMP)} DEFAULT CURRENT_TIMESTAMP,\n"
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

def update_db_categories(filename: Path):
    """ Update the database with the data in the categories JSON file. """
    # Get a database connection
    conn = get_db()

    # Open the categories JSON file and load the data
    with open(filename, 'r') as f:
        categories_json = json.load(f)

        # Load all the categories data into a list
        categories_new = []
        categories_update = []

        for category in categories_json:
            # Retrieve the data from the JSON object
            category_json = categories_json[category]

            data = {}
            data["name"] = category
            data["preferred_multimer"] = category_json["preferredMultimer"]
            if "shortName" in category_json:
                data["short_name"] = category_json["shortName"]
            else:
                data["short_name"] = None
            if "hasPage" in category_json:
                data["has_page"] = int(category_json["hasPage"])
            else:
                data["has_page"] = int(False)

            # Determine whether the category already exists and store the data in the correct list
            if conn.execute("SELECT id FROM categories WHERE name = ?", [category]).fetchone():
                categories_update.append(data)
            else:
                categories_new.append(data)

        # Insert the new categories into the database.
        if len(categories_new) > 0:
            sql = "INSERT INTO categories (name, preferred_multimer, short_name, has_page) VALUES (:name, :preferred_multimer, :short_name, :has_page)"
            conn.executemany(sql, categories_new)

        # Update the existing entries in the database.
        if len(categories_update) > 0:
            sql = "UPDATE categories SET preferred_multimer = :preferred_multimer, short_name = :short_name, has_page = :has_page WHERE name = :name"
            conn.executemany(sql, categories_update)

        # Commit the changes
        conn.commit()

def update_db_metadata(filename: Path):
    """ Update the database with the data in the metadata JSON file.  """
    # Get a database connection
    conn = get_db()

    # Set-up some useful variables
    search_fields = ((Field.search_fields() | Field.facet_fields()) & Field.metadata_fields()) - {Field.CATEGORY_ID}
    
    # Open the metadata JSON file and load the data
    with open(filename, 'r') as f:
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

        sql = "INSERT OR REPLACE INTO metadata (\n    "
        sql += ",\n    ".join(fields)
        sql += f",\n    {Field.CATEGORY_ID.db_name}\n)\n"
        sql += "SELECT\n    :"
        sql += ",\n    :".join(fields)
        sql += f",\n    categories.id\n"
        sql += "FROM categories\n"
        sql += f"WHERE name = :{Field.CATEGORY.db_name}"

        conn.executemany(sql, metadata)
        conn.commit()


def remove_db_entries(filename: Path):
    """ Remove all entries with a Uniprot ID in the give JSON file from the database. """   
    # Get a database connection
    conn = get_db()

    # Open the JSON file and load the data
    with open(filename, 'r') as f:
        remove_uids = [[uid] for uid in json.load(f)]

    # Set-up an SQL query to execute.
    #? This is hard-coded for now since rewriting ComparisonType and SQLCondition would require a code reorganization to avoid circular dependencies.
    sql = "DELETE FROM metadata\n"
    sql += f"WHERE {Field.UNIPROT_ID.db_name} = ?" 

    conn.executemany(sql, remove_uids)
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
@click.argument("db-filename", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("categories-filename", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option('-f', '--force', is_flag=True, help="Enables rewriting of the existing database file.")
def create(
    db_filename: Path,
    categories_filename: Path,
    force: bool = False
    ):
    """ Create a new database from the 'DB_FILENAME' and 'CATEGORIES_FILENAME' JSON files. """
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
    update_db_categories(categories_filename)

    # Fill the metadata table from the metadata json file.
    update_db_metadata(db_filename)

@bp.cli.command("update")
@click.argument("db-filename", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option('-c', '--categories-file', type=click.Path(exists=True, dir_okay=False, path_type=Path), help="A JSON file for supplying updates to the categories available in the database.")
def update(
    db_filename: Path,
    categories_file: Union[Path, None]
    ):
    """ 
        Updates the database based on the supplied JSON file.
        WARNING: Existing entries will be overwritten where needed.
    """
    # Update the categories table from the categories json file.
    #! FIXME: Temporarily disabled since it breaks category ids.
    if categories_file:
        update_db_categories(categories_file)
        # raise Exception("This feature has temporarily been disabled.")

    # Update the metadata table from the metadata json file.
    update_db_metadata(db_filename)

@bp.cli.command("remove")
@click.argument('filename', type=click.Path(exists=True, dir_okay=False, path_type=Path))
def remove(filename: Path):
    """ Remove all entries from the database that have an Uniprot ID that is found in the supplied JSON file. """
    remove_db_entries(filename)
