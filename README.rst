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

- Linux or macOS in a bash shell:::

    pythom -m venv .venv
    .venv/Scripts/activate
    pip install -r Requirements.txt

- Windows in a cmd shell:::

    python -m venv .venv
    .venv/Scripts/activate.bat
    python -m pip install -r Requirements.txt

- Windows in a PowerShell shell:::

    python -m venv .venv
    ./venv/Scripts/Activate.ps1
    python -m install -r Requirements.txt

Requirements
------------
First and foremost python needs to be installed on your system. How to install python depends on your Operating System.
In principle |python min| should work. However, the lowest version that has been tested is |python tested|.
You can determine the installed version of python as follows::

    python --version

``pip`` is the package manager for python. In most cases it comes with your installation, but you can verify it is
installed using:::

    pip --version

You can then install packages using pip with:::

    pip install [package_name]

This is the from that will be used in the rest of this document, but Windows users should keep in mind that the following
form is recommended for them instead:::

    python -m pip install

Virtual environment
-------------------
We recommend using a virtual environment to install al the dependencies for the webhost. This is most commonly done
using the ``venv`` package. ``venv`` can be installed using ``pip``.

Once installed, a new virtual environment can be created as follows:::

    python -m venv /path/to/venv

We recommend creating a local directory ``.venv`` to store your virtual environment.

In order to activate the virtual environment, got to ``/path/to/env/Scripts`` and run the activate script that corresponds
with your Operating System and shell. Once activated, any python command or code run will make use of the virtual environment
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

The ``--app prohistonedb`` can be left out by setting the environment variable ``FLASK_APP``.

When the server is running, by default it is bound to the localhost (127.0.0.1) with port 5000.

Testing
=======

Deployment
==========
