================
Sublime CLI
================

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT

This is a Python 3 CLI module for interacting with the Sublime email security platform.

Quick Start
===========
**Create a virtual environment (optional)**
::

  pip3 install virtualenv
  virtualenv venv -p python3.7
  source venv/bin/activate

**Install the library**:

``python setup.py install``

**Save your configuration**:

``sublime setup -k <your-API-key>``

Usage
=====
::

    Usage: sublime [OPTIONS] COMMAND [ARGS]...

      Sublime CLI.

    Options:
      -h, --help  Show this message and exit.

    Commands:
      analyze   Analyze an enriched MDM or raw EML.
      create    Create an item in your Sublime environment.
      delete    Delete an item(s) in your Sublime environment.
      enrich    Enrich an EML.
      get       Get items from your Sublime environment.
      help      Show this message and exit.
      listen    Listen for real-time events occuring in your Sublime...
      query     Query an enriched MDM and get the output.
      repl      Start an interactive shell.
      send      Send or generate mock data.
      setup     Configure API key.
      update    Update an item(s) in your Sublime environment.
      version   Get version and OS information for your Sublime commandline...


      Usage: sublime [OPTIONS] COMMAND [ARGS]...


Development
===========
**Override defaults**

``export BASE_URL=http://127.0.0.1:8000``

``export PYTHONPATH=/path/to/sublime-cli/src/``

``export BASE_WEBSOCKET=ws://127.0.0.1:8000``
