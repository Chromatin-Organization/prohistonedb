""" A module for testing the application factory. """
#***===== Imports =====***#
#*----- PyTest -----*#
import pytest

#*----- Main package imports -----*#
import prohistonedb

#*----- Standard library -----*#

#*----- Flask & Flask Extenstions -----*#

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local (test) imports -----*#

#***===== Tests =====***#
def test_config():
    """ Make sure that the application factory correctly takes in a testing configuration. """
    assert not prohistonedb.create_app().testing
    assert prohistonedb.create_app({"TESTING": True, "SECRET_KEY": "test"})

def test_fixture(app):
    """ Make sure that the app fixture uses a proper test configuration. """
    assert app.testing
    assert app.config["SECRET_KEY"] == "test"
    