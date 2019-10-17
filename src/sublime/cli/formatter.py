# coding=utf-8
"""Output formatters."""

from __future__ import print_function

import re
import functools
import json
from xml.dom.minidom import parseString

import gron
import ansimarkup
import click
import colorama
from jinja2 import Environment, PackageLoader

JINJA2_ENV = Environment(loader=PackageLoader("sublime.cli"))

colorama.init()
ANSI_MARKUP = ansimarkup.AnsiMarkup(
    tags={
        "header": ansimarkup.parse("<bold>"),
        "key": ansimarkup.parse("<blue>"),
        "value": ansimarkup.parse("<green>"),
        "noise": ansimarkup.parse("<light-yellow>"),
        "not-detected": ansimarkup.parse("<dim>"),
        "fail": ansimarkup.parse("<light-red>"),
        "unknown": ansimarkup.parse("<dim>"),
        "detected": ansimarkup.parse("<light-green>"),
    }
)


def colored_output(function):
    """Decorator that converts ansi markup into ansi escape sequences.

    :param function: Function that will return text using ansi markup.
    :type function: callable
    :returns: Wrapped function that converts markup into escape sequences.
    :rtype: callable

    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        output = function(*args, **kwargs)
        return ANSI_MARKUP(output)

    return wrapper


def json_formatter(result, _verbose):
    """Format result as json."""
    return json.dumps(result, indent=4)


@colored_output
def analyze_formatter(results, verbose):
    """Convert Analyze output into human-readable text."""
    template = JINJA2_ENV.get_template("analyze_result.txt.j2")
    return template.render(results=results["results"], verbose=verbose)


@colored_output
def mdm_formatter(results, verbose):
    """Convert Message Data Model into human-readable text."""
    gron_output = gron.gron(json.dumps(results))
    gron_output = gron_output.replace('json = {}', 'message_data_model = {}')
    gron_output = re.sub(r'\njson\.', '\n', gron_output)

    return gron_output

    # template = JINJA2_ENV.get_template("message_data_model.txt.j2")
    # return template.render(results=results, verbose=verbose)


FORMATTERS = {
    "json": json_formatter,
    "txt": {
        "enrich": mdm_formatter,
        "analyze": analyze_formatter
    },
}
