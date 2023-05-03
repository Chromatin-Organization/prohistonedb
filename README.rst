.. |prohistonedb| replace:: ProHistoneDB
.. |python| replace:: ``Python``
.. |python min| replace:: ``Python 3.7+``
.. |python tested| replace:: ``Python 3.9.15``
.. |flask| replace:: ``Flask``

.. |pip| replace:: ``pip``
.. |venv| replace:: ``venv``
.. |pytest| replace:: ``pytest``

.. |db| replace:: ``sqlite3``
.. |categories| replace:: ``categories.json``
.. |metadata| replace:: ``db.json``
.. |config| replace:: ``config.json``

======================
|prohistonedb| website
======================
[Description here]


TL;DR
=====
It is assumed that you have |python|, |pip| and |venv| installed and that |metadata| and 
|categories| are located in the ``instance`` directory in the project's root. Currently the raw data
folder is assumed to be at ``static/data``, but that should change in the near future. In order to
prepare the application, execute one of the following sets of commands when inside the root
directory of the project:

- Linux or macOS in a bash shell::

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r Requirements.txt
    flask database create

- Windows in a cmd shell::

    python3 -m venv .venv
    .venv/Scripts/activate.bat
    python3 -m pip install -r Requirements.txt
    flask database create

- Windows in a PowerShell shell::

    python3 -m venv .venv
    ./venv/Scripts/Activate.ps1
    python3 -m pip install -r Requirements.txt
    flask database create

Once the application has been set-up, you can run the development server with::

    flask run

Please note that it is advised to use a dedicated WSGI server in a deployment environment.

If you're contributing and want to receive tracebacks when running the server, use::

    flask run --debug

However, please only use this method when running locally. Running in debug mode is a security risk
when opened up to remote access.

Installation
============
Requirements
------------
First and foremost, |python| needs to be installed on your system. How to install python depends
on your Operating System. In principle |python min| should work. However, the lowest version that
has been tested is |python tested|. You can determine the installed version of python as follows::

    python3 --version

|pip| is the package manager for python. In most cases it comes with your installation, but you
can verify it is installed using::

    pip --version

You can then install packages using |pip| with::

    pip install [package_name]

This is the form that will be used in the rest of this document. However, Windows users should keep 
in mind that the following form is recommended for them instead::

    python3 -m pip install [package_name]

Virtual environment
-------------------
We recommend using a virtual environment to install al the dependencies for the webhost. This is
most commonly done using the |venv| package. |venv| can be installed using |pip|.

Once installed, a new virtual environment can be created as follows::

    python3 -m venv /path/to/venv

We recommend creating a local directory ``.venv`` to store your virtual environment.

How to activate your virtual environment depends on your operating system. In the case of Linux or 
macOS, you should execute the command::

    source /path/to/venv/bin/activate

In the case of Windows you should run either the ``\path\to\venv\Scripts\activate.bat`` or 
``\path\to\venv\Scripts\Activate.ps1`` file depending on whether you use cmd or PowerShell
respectively.

Once activated, any python command or code run will make use of the virtual environment
and any packages installed using |pip| will be installed into the virtual environment.

Requirements.txt
----------------
The file ``Requirements.txt`` contains all the information that |pip| needs in order install the 
required packages. To perform this installation, use the command:::

    pip install -r Requirements.txt

Currently this file also contains packages used for the purpose of development and testing. In
future these might be separated from the packages required for deployment.

Creating database
-----------------
The server application uses an |db| database in order to make the entries searchable. Before running
the app for the first time, this database must be created. It does this based on two JSON files. One
that contains all the relevant metadata from UniProt (|metadata| in the instance directory by 
default) and one that specifies the histone categories and their relevant properties (|categories| 
in the instance directory by default). In future these files will be generated or downloaded 
automatically, but for now these files must be placed in the configured instance directory location
manually.

Once the files have been prepared, the initial database can be created using the command::

    flask --app prohistonedb database create

Environment Variables
=====================
When working with the |prohistonedb| web application, it may be needed to run |flask| commands from
time to time. The command used to create the innitial database is a good example. All |flask|
commands support using environment variables as a replacement for any command line option. 

The format for these environment variables is ``FLASK_[OPTION]`` for any options of the base flask
command. For example, setting ``FLASK_APP=prohistonedb`` can be used to avoid adding ``--app 
prohistonedb`` to all flask commands related to this web application. The command for creating a 
database would then become::

    flask database create

When setting the environment variable for the command line option of a specific sub-command the 
format becomes ``FLASK_[SUB-COMMAND]_[OPTION]`` instead of ``FLASK_[OPTION]``. This  same pattern
repeats itself for sub-commands of sub-commands.

Dotenv files
------------
If ``python-dotenv`` is installed in the virtual environment, the use of ``.env`` and ``.flaskenv``
files to set environment variables is supported. The ``.flaskenv`` file is read first, followed by
the ``.env`` file. Both files are proccesed before any environment variables set in the command line
and are assumed to be at the location where the command is run or any of the folders higher up in
the file system hierarchy.

The repository contains a ``.flaskenv`` file with some default options to facilitate running flask
commands in the project's root directory during development. Since the ``Requirements.txt``
also contains ``python-dotenv`` any other |flask| commands mentioned in this document will assume
that the ``.flaskenv`` environment variables are set. When overwriting these settings,
please adapt your |flask| commands accordingly.

Instance Directory
==================
|flask| makes use of what is called the instance directory. This folder should contains all files
that are local to the machine that the server is deployed to and is created automatically when the
server is run for the first time. By default this includes the |db| database and the JSON files 
|categories| and |metadata| that are used for building the database. It can also contain an optional
|config| file where all the default settings for the server can be changed.

Config
======
The ``default_config.json`` file in the project's root directory contains the default configuration
for the server. Any local changes to this default configuration can be provided in a |config| file
in the instance directory.

The possible configuration settings include:
  * **DATABASE**: The location of ``sqlite3`` database file. It is assumed to be in the instance 
    directory if the path is relative.
  * **METADATA_JSON**: The location of the JSON file with metadata from 
    `UniProt <https://www.uniprot.org/>`_. It is assumed to be in the instance directory if the path 
    is relative.
  * **CATEGORIES_JSON**: The location of the JSON files that specifies the histone caregories. It is 
    assumed to be in the instance directory if the path is relative.
  * All builtin configuration values used by Flask: 
    `documentation <https://flask.palletsprojects.com/en/2.2.x/config/#builtin-configuration-values>`_

Testing
=======
Running tests requires the |pytest| package. In order to run the tests, simply run |pytest| in
the project's root directory. When contributing to the projects, please do this before any git
pushes to the server to make sure everything is in working order.

The tests run with their own server configuration which uses a temporary |db| database file to avoid
breaking the deployed database. When writing tests this is taken care of by the ``app`` fixture.

Usage
=====
Development server
------------------
In order to run the development server, run the command::

    flask run

During development it is advised to run in debug mode by adding the ``--debug`` option or by setting
the ``FLASK_DEBUG`` environment variable in order to automatically restart the server after code
changes and catch tracebacks. However, never do this in a deployment environment.

The running server by default bound to the localhost (127.0.0.1) on port 5000, but these can be
changed with |flask| command line options.

Database CLI commands
---------------------
As mentioned during the installation instructions, a new database can be created by using the
command::

    flask database create

If, for any reason, the database needs to be rewritten completely, this command includes a 
``--force`` option to overwrite any existing database. Use this with caution since the old database
will be lost. It is advised to back-up the old database before attempting this.

The database can also be updated without deltion if the database does not need to be restructured.
This will often be the case when |metadata| and |categories| files have been updated with new
histones or information. In these situation, please use the command::

    flask database update

This will update the database entries without deleting and rebuilding the entire database. It should
be noted that this will still overwrite existing entries if they are both in the existing database
and the new |metadata| and |categories| files. It is thus still advised to back-up the old database
before attempting the update.

Deployment
==========
