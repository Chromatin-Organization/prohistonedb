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
It is assumed that you have ``Python``, ``pip`` and ``venv`` installed.

- Linux or macOS in a bash shell::

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r Requirements.txt

- Windows in a cmd shell::

    python3 -m venv .venv
    .venv/Scripts/activate.bat
    python3 -m pip install -r Requirements.txt

- Windows in a PowerShell shell::

    python3 -m venv .venv
    ./venv/Scripts/Activate.ps1
    python3 -m pip install -r Requirements.txt

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

This is the from that will be used in the rest of this document, but Windows users should keep in mind that the following
form is recommended for them instead::

    python3 -m pip install [package_name]

Virtual environment
-------------------
We recommend using a virtual environment to install al the dependencies for the webhost. This is most commonly done
using the ``venv`` package. ``venv`` can be installed using ``pip``.

Once installed, a new virtual environment can be created as follows::

    python3 -m venv /path/to/venv

We recommend creating a local directory ``.venv`` to store your virtual environment.

How to activate your virtual environment depends on your operating system. In the case of Linux or macOS, you should run::

    source /path/to/venv/bin/activate

In the case of Windows you should run either ``\path\to\venv\Scripts\activate.bat`` or ``\path\to\venv\Scripts\Activate.ps1``
depending on whether you use cmd or PowerShell.

Once activated, any python command or code run will make use of the virtual environment
and any packages installed using pip will be installed into the virtual environment.

Requirements.txt
----------------
The file ``Requirements.txt`` contains all the information that pip needs in order install the required packages.
To perform this installation, use the command:::

    pip install -r Requirements.txt

Currently this file also contains packages used for the purpose of development and testing. In future these might be 
separated from the packages required for deployment.

Usage
=====
In order to run the development server, run the command::

    flask --app prohistonedb run

During development it is advised to run in debug mode in order to automatically restart the server after code changes
and catch tracebacks. However, never do this in a deployment environment.

The ``--app prohistonedb`` part can be left out of the command by setting the environment variable ``FLASK_APP``.

The running server by default bound to the localhost (127.0.0.1) on port 5000.

Instance Directory
==================
Once the server is running, an instance folder will be created. The folder contains all files that are local to the
machine that the server is deployed to. This includes files such as the sqlite database, the raw structure data and
a ``config.json`` file.

Config
======
The ``default_config.json`` file in the project's root directory contains the default configuration for the server.
Any local changes to this default configuration can be provided in a ``config.json`` file in the instance directory.

The possible configuration settings include:
  * **DATABASE**: The location of sqllite database file. Is assumed to be in the instance directory if the path is relative.
  * **METADATA_JSON**: The location of the json file with metadata from `UniProt <https://www.uniprot.org/>`_. Is assumed to be in the instance directory if the path is relative.
  * **CATEGORIES_JSON**: The location of the json files that specifies the histone caregories. Is assumed to be in the instance directory if the path is relative.
  * All builtin configuration values used by Flask: `documentation <https://flask.palletsprojects.com/en/2.2.x/config/#builtin-configuration-values>`_

Testing
=======
Running tests requires the ``pytest`` package. In order to run the tests, simply run ``pytest`` in the project's root
directory. When contributing to the projects, please do this before any git pushes to the server to make sure everything
is in working order.

The tests run with their own server configuration which. When writing tests this is taken care of by the ``app`` fixture.

Deployment
==========
