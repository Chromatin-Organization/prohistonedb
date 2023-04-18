.. |python min| replace:: ``Python 3.7+``
.. |python tested| replace:: ``Python 3.9.15``

====================
ProHistoneDB website
====================
[Description here]

Installation
============
TL;DR
-----
It is assumed that you have ``Python``, ``pip`` and ``venv`` installed and that ``db.json`` and ``categories.json``
are located in the instance directory. In order to prepare the application, execute on of the following sets of
commands:

- Linux or macOS in a bash shell::

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r Requirements.txt
    flask --app prohistonedb database create

- Windows in a cmd shell::

    python3 -m venv .venv
    .venv/Scripts/activate.bat
    python3 -m pip install -r Requirements.txt
    flask --app prohistonedb database create

- Windows in a PowerShell shell::

    python3 -m venv .venv
    ./venv/Scripts/Activate.ps1
    python3 -m pip install -r Requirements.txt
    flask --app prohistonedb database create

Requirements
------------
First and foremost python needs to be installed on your system. How to install python depends on your Operating System.
In principle |python min| should work. However, the lowest version that has been tested is |python tested|.
You can determine the installed version of python as follows::

    python3 --version

``pip`` is the package manager for python. In most cases it comes with your installation, but you can verify it is
installed using:::

    pip --version

You can then install packages using pip with::

    pip install [package_name]

This is the form that will be used in the rest of this document, but Windows users should keep in mind that the following
form is recommended for them instead::

    python3 -m pip install [package_name]

Virtual environment
-------------------
We recommend using a virtual environment to install al the dependencies for the webhost. This is most commonly done
using the ``venv`` package. ``venv`` can be installed using ``pip``.

Once installed, a new virtual environment can be created as follows::

    python3 -m venv /path/to/venv

We recommend creating a local directory ``.venv`` to store your virtual environment.

How to activate your virtual environment depends on your operating system. In the case of Linux or macOS, you should
execute the command::

    source /path/to/venv/bin/activate

In the case of Windows you should run either the ``\path\to\venv\Scripts\activate.bat`` or 
``\path\to\venv\Scripts\Activate.ps1`` file depending on whether you use cmd or PowerShell respectively.

Once activated, any python command or code run will make use of the virtual environment
and any packages installed using pip will be installed into the virtual environment.

Requirements.txt
----------------
The file ``Requirements.txt`` contains all the information that pip needs in order install the required packages.
To perform this installation, use the command:::

    pip install -r Requirements.txt

Currently this file also contains packages used for the purpose of development and testing. In future these might be 
separated from the packages required for deployment.

Creating the database
---------------------
The server application uses an ``sqlite3`` database in order to make the entries searchable. Before running the app
for the first time, this database must be created. It does this based on two JSON files. One that contains all the 
metadata from UniProt (``db.json`` in the instance directory by default) and one that specifies the histone categories
with the prefered multimer for their histones (``categories.json`` in the instance directory by default). In future
these files will be generated or downloaded automatically, but for now these files must be placed in the configured
location manually.

Once the files have been prepared, the initial database can be created using the command::

    flask --app prohistonedb database create

The environment variable ``FLASK_APP`` can be set to ``prohistonedb`` in order to avoid typing the ``--app prohistonedb``
part in any of the flask commands.

Usage
=====
In order to run the development server, run the command::

    flask --app prohistonedb run

During development it is advised to run in debug mode in order to automatically restart the server after code changes
and catch tracebacks. However, never do this in a deployment environment.

As with the database creation, the ``--app prohistonedb`` part can be left out of flask commands by setting the environment
variable ``FLASK_APP``.

The running server by default bound to the localhost (127.0.0.1) on port 5000.

Instance Directory
==================
After launching the app for the first time, an instance folder will be created. The folder contains all files that are
local to the machine that the server is deployed to. By default this includes the ``sqlite3`` database, the raw structure data,
and the JSON files with the categories and metadata for building the database. It can also contain an optional
``config.json`` file where all the default settings for the server can be changed.

Config
======
The ``default_config.json`` file in the project's root directory contains the default configuration for the server.
Any local changes to this default configuration can be provided in a ``config.json`` file in the instance directory.

The possible configuration settings include:
  * **DATABASE**: The location of ``sqlite3`` database file. It is assumed to be in the instance directory if the path is relative.
  * **METADATA_JSON**: The location of the JSON file with metadata from `UniProt <https://www.uniprot.org/>`_. It is assumed to be in the instance directory if the path is relative.
  * **CATEGORIES_JSON**: The location of the JSON files that specifies the histone caregories. It is assumed to be in the instance directory if the path is relative.
  * All builtin configuration values used by Flask: `documentation <https://flask.palletsprojects.com/en/2.2.x/config/#builtin-configuration-values>`_

Testing
=======
Running tests requires the ``pytest`` package. In order to run the tests, simply run ``pytest`` in the project's root
directory. When contributing to the projects, please do this before any git pushes to the server to make sure everything
is in working order.

The tests run with their own server configuration which uses a temporary ``sqlite3`` database file to avoid breaking
the deployed database. When writing tests this is taken care of by the ``app`` fixture.

Deployment
==========
