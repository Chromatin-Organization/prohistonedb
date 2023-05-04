""" A module defining all the models used in the database. """
#***===== Imports =====***#
#*----- Standard library -----*#
from dataclasses import dataclass
from enum import Enum

from typing import Optional, Union

from pathlib import Path

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#

#***===== Category Dataclass =====***#
@dataclass(eq=False, frozen=True)
class Category:
    """ A compound dataclass to hold a Category. If no short name is supplied, it will default to the standard name. """
    id: int
    name: str
    preferred_multimer: str
    short_name: Optional[str] = None

    def __post_init__(self):
        # If no short name was supplied, set it to the long name.
        if self.short_name is None:
            object.__setattr__(self, "short_name", self.name)    
