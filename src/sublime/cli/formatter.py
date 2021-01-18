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

JINJA2_ENV = Environment(loader=PackageLoader("sublime.cli"),
        extensions=['jinja2.ext.loopcontrols'])

colorama.init()
ANSI_MARKUP = ansimarkup.AnsiMarkup(
    tags={
        "header": ansimarkup.parse("<bold>"),
        "key": ansimarkup.parse("<cyan>"),
        "value": ansimarkup.parse("<green>"),
        "not-detected": ansimarkup.parse("<dim>"),
        "fail": ansimarkup.parse("<light-red>"),
        "success": ansimarkup.parse("<green>"),
        "unknown": ansimarkup.parse("<dim>"),
        "detected": ansimarkup.parse("<light-green>"),
        "enrichment": ansimarkup.parse("<light-yellow>"),
        "warning": ansimarkup.parse("<light-yellow>"),
        "query": ansimarkup.parse("<white>"),
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


def json_formatter(result, verbose=False):
    """Format result as json."""
    return json.dumps(result, indent=4)


@colored_output
def analyze_formatter(results, verbose):
    """Convert Analyze output into human-readable text."""
    template = JINJA2_ENV.get_template("analyze_result.txt.j2")

    # analyze/multi will return 'results', otherwise 'result'
    rule_results, query_results = results["rule_results"], results["query_results"]

    for result in rule_results:
        if result.get("source"):
            result["source"] = format_mql(result["source"])

    for result in query_results:
        if result.get("result") and isinstance(result["result"], dict):
            result["result"] = json_formatter(result["result"])

        if result.get("source"):
            result["source"] = format_mql(result["source"])

    return template.render(rules=rule_results, queries=query_results, verbose=verbose)


def mdm_formatter(results, verbose):
    """Convert Message Data Model into human-readable text."""
    gron_output = gron.gron(json.dumps(results))
    gron_output = gron_output.replace('json = {}', 'message_data_model = {}')
    gron_output = re.sub(r'\njson\.', '\n', gron_output)

    return gron_output

    # template = JINJA2_ENV.get_template("message_data_model.txt.j2")
    # return template.render(results=results, verbose=verbose)


def format_mql(mql):
    mql = mql.replace("&&", "\n  &&")
    mql = mql.replace("||", "\n  ||")
    mql = mql.replace("],", "],\n  ")

    return mql

@colored_output
def me_formatter(result, verbose):
    """Convert 'me' output into human-readable text."""
    template = JINJA2_ENV.get_template("me_result.txt.j2")

    return template.render(result=result, verbose=verbose)

@colored_output
def feedback_formatter(result, verbose):
    """Convert 'feedback' output into human-readable text."""
    template = JINJA2_ENV.get_template("feedback_result.txt.j2")

    return template.render(result=result, verbose=verbose)


FORMATTERS = {
    "json": json_formatter,
    "txt": {
        "me": me_formatter,
        "feedback": feedback_formatter,
        "create": mdm_formatter,
        "analyze": analyze_formatter
    },
}
