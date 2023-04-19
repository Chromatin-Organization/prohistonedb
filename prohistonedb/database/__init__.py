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
        raise Exception("A database file already exists.")
    
    # Create a database with empty tables.
    conn = get_db()

    conn.execute("""
        CREATE TABLE categories (
            name PRIMARY KEY,
            multimer NOT NULL CHECK( multimer IN ('monomer', 'dimer', 'tetramer', 'hexamer') )
        )
    """)

    conn.execute("""
        CREATE TABLE metadata (
            uniprot_id PRIMARY KEY,
            organism NOT NULL,
            organism_id NOT NULL,
            sequence NOT NULL,
            sequence_len NOT NULL,
            category NOT NULL,
            lineage NOT NULL,
            protein_id NOT NULL,
            proteome_id NOT NULL,
            gen_id,
            genome_id NOT NULL,
            CHECK (LENGTH (sequence) = sequence_len),
            FOREIGN KEY (category)
                REFERENCES categories 
        )
    """)
    conn.commit()

    # Fill the categories table from the categories json file.
    categories_json = Path(flask.current_app.config["CATEGORIES_JSON"])

    if not categories_json.is_file():
        raise Exception("Config option 'CATEGORIES_JSON' does not point to a file.")

    with open(categories_json, 'r') as f:
        categories = json.load(f)
        conn.executemany("INSERT INTO categories (name, multimer) VALUES (?, ?)", categories.items())
        conn.commit()

    # Fill the metadata table from the metadata json file.
    metadata_json = Path(flask.current_app.config["METADATA_JSON"])

    if not metadata_json.is_file():
        raise Exception("Config option 'METADATA_JSON' does not point to a file.")
    
    with open(metadata_json, 'r') as f:
        metadata_json = json.load(f)
        metadata = []

        for uid in metadata_json:
            print(uid)
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
        sql = """ 
            INSERT INTO metadata (
                uniprot_id,
                organism,
                organism_id,
                sequence,
                sequence_len,
                category,
                lineage,
                protein_id,
                proteome_id,
                gen_id,
                genome_id
            ) VALUES (
                :uniprot_id,
                :organism,
                :organism_id,
                :sequence,
                :sequence_len,
                :category,
                :lineage,
                :protein_id,
                :proteome_id,
                :gen_id,
                :genome_id
            )
        """
        conn.executemany(sql, metadata)
        conn.commit()
