""""""
#***===== Imports =====***#
#*----- Standard Library -----*#
from typing import Mapping, Any
from pathlib import Path

import logging.config

import json

#*----- Flask & Flask Extenstions -----*#
import flask
from flask import Flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#

#***===== Application Factory =====***#
def create_app(test_config: Mapping[str, Any] = None):
    """ Create the Flask app object. A test_config object can be used for testing. """
    #*----- Set variables for later usage -----*#
    root_dir = Path(__file__).parents[1].resolve()

    #*----- Configure logging -----*#
    logging_config = root_dir / Path("log_config.json")
    with open(logging_config) as f:
        logging.config.dictConfig(json.load(f))

    #*----- Create the app -----*#
    #? We might want to change the default instance folder for deployment.
    app = Flask(__name__)

    #*----- Change logging level when in debug mode -----*#
    if app.debug:
        app.logger.root.level = "DEBUG"
        app.logger.debug("Running in 'DEBUG' mode. Root logger's logging level has been set to debug.")

    #*----- Prepare the instance directory -----*#
    instance_dir = Path(app.instance_path).resolve()
    app.logger.info(f"Instance dear has been set to '{instance_dir}'.")

    if not instance_dir.is_dir():
        app.logger.info("Instance folder has not been found. Creating a new instance folder.")
        Path(app.instance_path).mkdir()

    #*----- Set the app's config -----*#
    root_dir = Path(__file__).parents[1].resolve()
    instance_dir = Path(app.instance_path).resolve()

    # First load the default config
    app.logger.info("Loading default server config...")
    app.config.from_file(root_dir / Path("default_config.json"), json.load)

    # Then check if a test Config object is supplied to the factory
    if test_config is None:
        # If this is not a test, read the config file that is supplied in the instance folder (for safety purposes).
        path = instance_dir / Path("config.json")

        if path.is_file():
            app.logger.info("Found additional 'config.json' in the instance directory. Loading local server config...")
            app.config.from_file(instance_dir / Path("config.json"), json.load)
    else:
        # If this is a test, read the config options from the supplied mapping
        app.logger.info("Found test configuration. Loading test config...")
        app.config.from_mapping(test_config)

    # Assume "METADATA_JSON", "CATEGORIES_JSON" and "DATABASE" are in the instance directory if the paths are relative.
    for config_param in ["DATABASE", "METADATA_JSON", "CATEGORIES_JSON"]:
        path = Path(app.config[config_param]) 

        if not path.is_absolute():
            app.config[config_param] = str(instance_dir / path)
            app.logger.info(f"'{config_param}' is a relative path. Destination set to '{app.config[config_param]}'.")

    #*----- Initialize the database -----*#
    app.logger.info("Initializing database...")
    from . import database
    database.init_app(app)

    #*----- Register Blueprints -----*#
    app.logger.info("Registering blueprints...")

    from . import types
    app.register_blueprint(types.bp)

    from . import main
    app.register_blueprint(main.bp)
    app.add_url_rule("/", endpoint="index") # Add index as an additional endpoint for the root.

    from . import search
    app.register_blueprint(search.bp)

    from . import categories
    app.register_blueprint(categories.bp)

    #*----- Return the constructed app -----*#
    app.logger.info("Application setup has been completed.")
    return app