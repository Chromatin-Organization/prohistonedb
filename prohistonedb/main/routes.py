""" The routes for the main endpoint. """
#***===== Imports =====***#
#*----- Standard library -----*#

#*----- Flask & Flask Extenstions -----*#
import flask
import jinja2

#*----- External packages -----*#

#*----- Custom packages -----*#

#*----- Local imports -----*#

#***===== Blueprint Import =====***#
from . import bp

#***===== Route Definitions =====***#
@bp.route("/", methods=["GET"])
def index():
    """ Render the index page. """
    #? Tim: What is the purpose of setting 'segment' and 'parent'? I don't see them used in your templates.
    try:
        return flask.render_template('pages/index.html.j2', segment='index', parent='pages')
    except jinja2.TemplateNotFound:
        return flask.render_template('pages/index.html.j2'), 404

#TODO: Different entry pages for different multimers.
@bp.route("/entry/<uniprotID>", methods=["GET"])
def entry(uniprotID: str):
    """ Render the structure page for a specified entry. """
    return flask.render_template('pages/entry.html.j2', uniprotID = uniprotID)

#? NOTE (Tim): I removed the superfluous '/' at the end of the URL. Let me know if you planned for multiple
#?             about pages, then I'll give it a separate blueprint.
@bp.route('/about')
def about():
    """ Render the about page. """
    return flask.render_template('pages/about.html.j2')

#? NOTE (Tim): I shortened the URL since we only have one categories page for now. For trailing slash see above note.
@bp.route('/categories')
def categories():
  return flask.render_template('pages/categories.html.j2')