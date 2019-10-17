================
Sublime CLI
================

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT

This is a Python 3 CLI module for interacting with the Sublime Phishing Defense framework.

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
      enrich    Enrich an EML.
      feedback  Send feedback directly to the Sublime team.
      help      Show this message and exit.
      repl      Start an interactive shell.
      setup     Configure API key.
      version   Get version and OS information for your Sublime commandline...

Development
===========
**Override defaults**

``export BASE_URL=http://127.0.0.1:8000``
