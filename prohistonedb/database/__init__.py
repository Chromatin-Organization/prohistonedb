""" A blueprint for mapping to the database package. """
#***===== Imports =====***#
#*----- Standard Library -----*#
from typing import Optional

from pathlib import Path

import json

#*----- Flask & Flask Extenstions -----*#
import flask
from flask import Flask

#*----- Other External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#
from . import connections
from .types import FieldType

#***===== Functions =====***#
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

#***===== Create Blueprint =====***#
bp  = flask.Blueprint("database", __name__, cli_group="database")

#***===== Register CLI commands =====***#
@bp.cli.command("create")
def create():
    """ Create a new database from json files. """
    #TODO: Automatically generate column names based on the possible FieldType values with SQL injection prevention.
    #TODO: Add CLI option for overwriting existing database file.
    #TODO: Split functionality into functions and only call them here.

    # Make sure the database file does not exist yet.
    database_path = Path(flask.current_app.config["DATABASE"])

    if database_path.is_file():
        database_path.unlink()
        # raise Exception("A database file already exists.")
    
    # Create a database with empty tables.
    conn = get_db()

    conn.execute("""
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            multimer TEXT NOT NULL CHECK( multimer IN ('monomer', 'dimer', 'tetramer', 'hexamer') ),
            short_name TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE metadata (
            uniprot_id TEXT PRIMARY KEY,
            organism TEXT NOT NULL,
            organism_id TEXT NOT NULL,
            sequence TEXT NOT NULL,
            sequence_len INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            lineage TEXT NOT NULL,
            protein_id TEXT NOT NULL,
            proteome_id TEXT NOT NULL,
            gen_id TEXT,
            genome_id TEXT NOT NULL,
            CHECK (LENGTH (sequence) = sequence_len),
            FOREIGN KEY (category_id)
                REFERENCES categories(id)
        )
    """)
    conn.commit()

    # Create a view for accessing the necessary data in a search
    conn.execute("""
        CREATE VIEW search AS
        SELECT metadata.*, categories.name AS category
        FROM metadata
        LEFT JOIN categories ON metadata.category_id = categories.id
    """)

    # Fill the categories table from the categories json file.
    categories_json = Path(flask.current_app.config["CATEGORIES_JSON"])

    if not categories_json.is_file():
        raise Exception("Config option 'CATEGORIES_JSON' does not point to a file.")

    with open(categories_json, 'r') as f:
        categories_json = json.load(f)
        categories = []

        for category in categories_json:
            category_json = categories_json[category]

            data = {}
            data["name"] = category
            data["multimer"] = category_json["preferedMultimer"]
            if "shortName" in category_json:
                data["short_name"] = category_json["shortName"]
            else:
                data["short_name"] = None
            
            categories.append(data)

        sql = "INSERT INTO categories (name, multimer, short_name) VALUES (:name, :multimer, :short_name)"
        conn.executemany(sql, categories)
        conn.commit()

    # Fill the metadata table from the metadata json file.
    metadata_json = Path(flask.current_app.config["METADATA_JSON"])

    if not metadata_json.is_file():
        raise Exception("Config option 'METADATA_JSON' does not point to a file.")
    
    with open(metadata_json, 'r') as f:
        metadata_json = json.load(f)
        metadata = []

        for uid in metadata_json:
            data = {}
            data[FieldType.UNIPROT_ID.db_name] = uid

            #TODO: Double check these with notes.
            #? Hardcoded for now. Do we want to change this?
            for field in FieldType:
                uid_json = metadata_json[uid]
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
                    lineages = [lineage["scientificName"] for lineage in uid_json["uniprot"]["lineages"]]
                    data[field.db_name] = json.dumps(lineages)
                elif field is FieldType.PROTEIN_ID:
                   ref_properties = [ref["properties"] for ref in cross_references]
                   pids = [property["value"] for properties in ref_properties for property in properties if property["key"] == "ProteinId"]
                   data[field.db_name] = json.dumps(pids)
                elif field is FieldType.PROTEOME_ID:
                    pmids = [ref["id"] for ref in cross_references if ref["database"] == "Proteomes"]
                    data[field.db_name] = json.dumps(pmids)
                elif field is FieldType.GEN_ID:
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
                elif field is FieldType.GENOME_ID:
                    gmids = [ref["id"] for ref in cross_references if ref["database"] == "EMBL"]
                    data[field.db_name] = json.dumps(gmids)
                else:
                    raise Exception(f"Unknown JSON path for FieldType {field}")
            
            metadata.append(data)
        
        #TODO: Automatically generate column names based on the possible FieldType values with SQL injection prevention.        
        sql = """INSERT INTO metadata (
                    uniprot_id,
                    organism,
                    organism_id,
                    sequence,
                    sequence_len,
                    category_id,
                    lineage,
                    protein_id,
                    proteome_id,
                    gen_id,
                    genome_id
                )
                SELECT
                    :uniprot_id,
                    :organism,
                    :organism_id,
                    :sequence,
                    :sequence_len,
                    categories.id,
                    :lineage,
                    :protein_id,
                    :proteome_id,
                    :gen_id,
                    :genome_id
                FROM categories
                    WHERE name = :category
        """
        
        conn.executemany(sql, metadata)
        conn.commit()
