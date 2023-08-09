""" A module defining custom types that are used by session cookies. """
#***===== Feature Imports =====***#
from __future__ import annotations

#***===== Imports =====***#
#*----- Standard library -----*#
from dataclasses import dataclass

#*----- Flask & Flask extenstions -----*#
import flask

#*----- Other external packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#
from ..database.models import Organism

#***===== CartItem Class =====***#
@dataclass(eq=False, frozen=True)
class CartItem:
    uniprot_id: str
    organism_name: str