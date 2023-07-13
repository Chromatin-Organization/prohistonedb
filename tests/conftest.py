""" Configuration script for pytest. """
#***===== Imports =====***#
#*----- PyTest -----*#
import pytest

#*----- Standard library -----*#
import sys
from pathlib import Path

#*----- Flask & Flask Extenstions -----*#
import flask
from flask import Flask

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local (test) imports -----*#

#***===== Add & Import Main Package =====***#
sys.path.append(str(Path(__file__).parents[1].resolve()))
print(sys.path)
import prohistonedb

#***===== Fixtures =====***#
#*----- App fixture -----*#
@pytest.fixture
def app() -> Flask:
    """ Create an instance of the Flask app for testing. """
    #* Preparation *#
    #TODO: Change the database that is accessed during testing.
    app = prohistonedb.create_app(
        test_config = {
            "TESTING": True,
            "SECRET_KEY": "test"
        }
    )

    #* Yield for testing *#
    yield app
    #* Clean up *#

#*----- Client fixture -----*#
@pytest.fixture
def client():
    """ Create a client capable of making server requests for testing. """
    return app.test_client()

#*----- CLI runner fixture -----*#
@pytest.fixture
def runner():
    """ Create a runner capable of executing CLI commands for testing. """