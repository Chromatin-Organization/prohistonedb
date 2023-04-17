""""""
#***===== Imports =====***#
#*----- Standard Library -----*#
from typing import Mapping, Any
from pathlib import Path

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
    
    #*----- Create the app -----*#
    #? We might want to change the default instance folder for deployment.
    app = Flask(__name__)

    #*----- Set the app's config -----*#
    root_dir = Path(__file__).parents[1].resolve()
    instance_dir = Path(app.instance_path).resolve()

    # First load the default config
    app.config.from_file(root_dir / Path("default_config.json"), json.load)

    # Then check if a test Config object is supplied to the factory
    if test_config is None:
        # If this is not a test, read the config file that is supplied in the instance folder (for safety purposes).
        app.config.from_file(instance_dir / Path("config.json"), json.load, silent=True)
    else:
        # If this is a test, read the config options from the supplied mapping
        app.config.from_mapping(test_config)

    # Assume "METADATA_JSON", "CATEGORIES_JSON" and "DATABASE" are in the instance directory if the paths are relative.
    for config_param in ["DATABASE", "METADATA_JSON", "CATEGORIES_JSON"]:
        path = Path(app.config[config_param]) 

        if not path.is_absolute():
            app.config["DATABASE"] = str(instance_dir / path)

    #*----- Prepare the instance folder -----*#
    Path(app.instance_path).mkdir(exist_ok=True)

    #*----- Initialize the database -----*#
    from . import database
    database.init_app(app)

    #*----- Register Blueprints -----*#
    from . import main
    app.register_blueprint(main.bp)
    app.add_url_rule("/", endpoint="index") # Add index as an additional endpoint for the root.

    from . import search
    app.register_blueprint(search.bp)

    from . import categories
    app.register_blueprint(categories.bp)

    #*----- Return the constructed app -----*#
    return app