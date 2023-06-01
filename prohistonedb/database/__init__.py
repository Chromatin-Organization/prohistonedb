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
from ..search.types import FieldType
from .models import Multimer

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

#***===== Other Functions =====***#
#TODO: Add automatic column names for categories table.
#TODO: Automatically determine column names for non-searchable fields.
#TODO: Add field info (such as variable type).
def init_db():
    """ Creates a database with empty tables and corresponding indexes. """ 
    # Create the database
    conn = get_db()

    # Create the categories table
    flask.current_app.logger.info(f"Creating the categories table.")
    multimer_options =  "', '".join([multimer.value for multimer in Multimer])
    conn.execute(f"""
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            preferred_multimer TEXT NOT NULL CHECK( preferred_multimer IN ('{multimer_options}') ),
            short_name TEXT,
            has_page INTEGER NOT NULL CHECK( has_page IN (0, 1) )
        )
    """)

    # Add indexes for the categories table
    conn.execute("CREATE INDEX idx_name ON categories(name)")

    # Create the metadata table
    flask.current_app.logger.info(f"Creating the metadata table.")
    conn.execute(f"""
        CREATE TABLE metadata (
            {FieldType.UNIPROT_ID.db_name} TEXT PRIMARY KEY,
            {FieldType.ORGANISM.db_name} TEXT NOT NULL,
            {FieldType.ORGANISM_ID.db_name} TEXT NOT NULL,
            {FieldType.SEQUENCE.db_name} TEXT NOT NULL,
            {FieldType.SEQUENCE_LEN.db_name} INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            {FieldType.LINEAGE.db_name} TEXT NOT NULL,
            {FieldType.LINEAGE.db_name}_json TEXT NOT NULL,
            {FieldType.PROTEIN_IDS.db_name} TEXT NOT NULL,
            {FieldType.PROTEOME_IDS.db_name} TEXT,
            {FieldType.GENES.db_name} TEXT,
            {FieldType.GENOME_IDS.db_name} TEXT NOT NULL,
            rel_path TEXT NOT NULL,
            ranks TEXT,
            FOREIGN KEY (category_id)
                REFERENCES categories(id)
        )
    """)

    # Add indexes for the metadata table
    flask.current_app.logger.info(f"Creating indexes for the metadata table.")
    conn.execute(f"CREATE INDEX idx_{FieldType.ORGANISM.db_name} ON metadata({FieldType.ORGANISM.db_name})")
    conn.execute(f"CREATE INDEX idx_{FieldType.ORGANISM_ID.db_name} ON metadata({FieldType.ORGANISM_ID.db_name})")
    conn.execute(f"CREATE INDEX idx_{FieldType.SEQUENCE.db_name} ON metadata({FieldType.SEQUENCE.db_name})")
    conn.execute(f"CREATE INDEX idx_{FieldType.SEQUENCE_LEN.db_name} ON metadata({FieldType.SEQUENCE_LEN.db_name})")
    conn.execute(f"CREATE INDEX idx_category_id ON metadata(category_id)")
    conn.execute(f"CREATE INDEX idx_{FieldType.LINEAGE.db_name} ON metadata({FieldType.LINEAGE.db_name})")
    conn.execute(f"CREATE INDEX idx_{FieldType.PROTEIN_IDS.db_name} ON metadata({FieldType.PROTEIN_IDS.db_name})")
    conn.execute(f"CREATE INDEX idx_{FieldType.PROTEOME_IDS.db_name} ON metadata({FieldType.PROTEOME_IDS.db_name})")
    conn.execute(f"CREATE INDEX idx_{FieldType.GENES.db_name} ON metadata({FieldType.GENES.db_name})")
    conn.execute(f"CREATE INDEX idx_{FieldType.GENOME_IDS.db_name} ON metadata({FieldType.GENOME_IDS.db_name})")

    # Create a view for accessing the necessary data in a search
    conn.execute(f"""
        CREATE VIEW search AS
            SELECT metadata.*, categories.name AS {FieldType.CATEGORY.db_name}, categories.preferred_multimer
            FROM metadata
            LEFT JOIN categories ON metadata.category_id = categories.id
    """)

    # Commit the changes to the database
    conn.commit()

#TODO: Automatically generate column names.
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

#TODO: Automatically generate column names.
#? The JSON paths in the metadata JSON file for the columns are currently hard-coded. Do we want to change this?
def update_db_metadata():
    """ Update the database with the data in the metadata JSON file.  """
    # Get a database connection
    conn = get_db()

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
            data[FieldType.UNIPROT_ID.db_name] = uid
            uid_json = metadata_json[uid]

            # Add the searchable fields
            #* Currently hard-coded!
            for field in FieldType:
                cross_references = uid_json["uniprot"]["uniProtKBCrossReferences"]

                if field is FieldType.UNIPROT_ID:
                    data[field.db_name] = uid
                elif field is FieldType.ORGANISM:
                    data[field.db_name] = uid_json["uniprot"]["organism"]["scientificName"]
                elif field is FieldType.ORGANISM_ID:
                    data[field.db_name] = uid_json["uniprot"]["organism"]["taxonId"]
                elif field is FieldType.SEQUENCE:
                    data[field.db_name] = uid_json["uniprot"]["sequence"]["value"]
                elif field is FieldType.SEQUENCE_LEN:
                    data[field.db_name] = uid_json["uniprot"]["sequence"]["length"]
                elif field is FieldType.CATEGORY:
                    data[field.db_name] = uid_json["histoneDB"]["category"]
                elif field is FieldType.LINEAGE:
                    lineages_full = uid_json["uniprot"]["lineages"]
                    lineage_names = [lineage["scientificName"] for lineage in lineages_full]
                    data[field.db_name] = json.dumps(lineage_names)
                    data[field.db_name + "_json"] = json.dumps(lineages_full)
                elif field is FieldType.PROTEIN_IDS:
                    ref_properties = [ref["properties"] for ref in cross_references]
                    pids = [property["value"] for ref in ref_properties for property in ref if property["key"] == "ProteinId"]
                    if pids:
                        data[field.db_name] = json.dumps(pids)
                    else:
                        data[field.db_name] = None
                elif field is FieldType.PROTEOME_IDS:
                    pmids = [ref["id"] for ref in cross_references if ref["database"] == "Proteomes"]
                    if pmids:
                        data[field.db_name] = json.dumps(pmids)
                    else:
                        data[field.db_name] = None
                elif field is FieldType.GENES:
                    if not "genes" in uid_json["uniprot"].keys():
                        data[field.db_name] = None
                        continue

                    for gen in uid_json["uniprot"]["genes"]:
                        if "geneName" in gen.keys():
                            gids = [gen["geneName"]["value"]]
                        elif "orfNames" in gen.keys():
                            gids = [orf_name["value"] for orf_name in gen["orfNames"]]
                        else:
                            data[field.db_name] = None
                            continue
                    
                    data[field.db_name] = json.dumps(gids)
                elif field is FieldType.GENOME_IDS:
                    gmids = [ref["id"] for ref in cross_references if ref["database"] == "EMBL"]
                    if gmids:
                        data[field.db_name] = json.dumps(gmids)
                    else:
                        data[field.db_name] = None
                else:
                    raise Exception(f"Unknown JSON path for FieldType {field}")
            
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

            # Apply all the fields for this uid
            metadata.append(data)

        # Execute the SQL query on the database      
        sql = f"""INSERT INTO metadata (
                    {FieldType.UNIPROT_ID.db_name},
                    {FieldType.ORGANISM.db_name},
                    {FieldType.ORGANISM_ID.db_name},
                    {FieldType.SEQUENCE.db_name},
                    {FieldType.SEQUENCE_LEN.db_name},
                    category_id,
                    {FieldType.LINEAGE.db_name},
                    {FieldType.LINEAGE.db_name}_json,
                    {FieldType.PROTEIN_IDS.db_name},
                    {FieldType.PROTEOME_IDS.db_name},
                    {FieldType.GENES.db_name},
                    {FieldType.GENOME_IDS.db_name},
                    rel_path,
                    ranks
                )
                SELECT
                    :{FieldType.UNIPROT_ID.db_name},
                    :{FieldType.ORGANISM.db_name},
                    :{FieldType.ORGANISM_ID.db_name},
                    :{FieldType.SEQUENCE.db_name},
                    :{FieldType.SEQUENCE_LEN.db_name},
                    categories.id,
                    :{FieldType.LINEAGE.db_name},
                    :{FieldType.LINEAGE.db_name}_json,
                    :{FieldType.PROTEIN_IDS.db_name},
                    :{FieldType.PROTEOME_IDS.db_name},
                    :{FieldType.GENES.db_name},
                    :{FieldType.GENOME_IDS.db_name},
                    :rel_path,
                    :ranks
                FROM categories
                    WHERE name = :{FieldType.CATEGORY.db_name}
        """
        
        conn.executemany(sql, metadata)
        conn.commit()

def delete_db():
    db_path = Path(flask.current_app.config["DATABASE"])
    db_path.unlink(missing_ok=True)

#***===== Create Blueprint =====***#
bp  = flask.Blueprint("database", __name__, cli_group="database")

#***===== Register Template Filters =====***#
@bp.app_template_filter("field_name")
def field_name(s: str) -> str:
    if s == "any":
        return s
    
    return str(FieldType(s))


#***===== Register Jinja Context Processors =====***#
@bp.app_context_processor
def inject_max_sequence_length():
    db = get_db()
    max_seq_len = db.execute(f"SELECT MAX({FieldType.SEQUENCE_LEN.db_name}) FROM search").fetchone()[0]
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
