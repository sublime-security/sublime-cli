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


def json_formatter(result, verbose=False, indent=4, offset=0):
    """Format result as json."""
    string = json.dumps(result, indent=indent)
    string = string.replace("\n", "\n" + "  "*offset)
    return string


@colored_output
def analyze_formatter(results, verbose):
    """Convert Analyze output into human-readable text."""
    if len(results) > 1:
        mql_offset = 5
        json_offset = 4
        template = JINJA2_ENV.get_template("analyze_multi.txt.j2")
    else:
        mql_offset = 3
        json_offset = 2
        template = JINJA2_ENV.get_template("analyze.txt.j2")
    
    # calculate total stats
    sample_result = next(iter(results.values()))
    summary_stats = {
        'total_messages': len(results),
        'total_rules': len(sample_result['rule_results']),
        'total_queries': len(sample_result['query_results']),
    }
    rules = [rule for rule in sample_result['rule_results']]
    queries = [query for query in sample_result['query_results']]
    
    # separate matched/unmatched messages and distinguish flagged/unflagged rules
    flagged_messages = []
    unflagged_messages = []
    all_flagged_rules = set()
    for _, result in results.items():
        normal_queries = []
        falsey_queries = []
        failed_queries = []
        for query in result['query_results']:
            if query['result']:
                normal_queries.append(query)
            elif query['success']:
                falsey_queries.append(query)
            else:
                failed_queries.append(query)
        result['normal_query_results'] = normal_queries
        result['falsey_query_results'] = falsey_queries
        result['failed_query_results'] = failed_queries

        flagged_rules = []
        unflagged_rules = []
        failed_rules = []
        for rule in result['rule_results']:
            if rule['result']:
                flagged_rules.append(rule)
                all_flagged_rules.add(rule['name']+rule['source']) # no unique identifier
            elif rule['success']:
                unflagged_rules.append(rule)
            else:
                failed_rules.append(rule)
        result['flagged_rule_results'] = flagged_rules
        result['unflagged_rule_results'] = unflagged_rules
        result['failed_rule_results'] = failed_rules

        if len(flagged_rules) > 0:
            flagged_messages.append(result)
        else:
            unflagged_messages.append(result)
        
    # calculate flagged stats
    summary_stats['flagged_rules'] = len(all_flagged_rules)
    summary_stats['flagged_messages'] = len(flagged_messages)

    # format mql and json outputs
    for msg in flagged_messages + unflagged_messages: 
        for result in msg['rule_results'] + msg['query_results']:
            if 'source' in result:
                result['source'] = format_mql(result['source'], offset=mql_offset)

            if 'result' in result and isinstance(result['result'], dict) or isinstance(result['result'], list):
                result['result'] = json_formatter(
                        result['result'],
                        offset=json_offset,
                        indent=2)

    # TO DO: sort each list of messages by extension and file name (or directory?)

    return template.render(
            stats=summary_stats,
            flagged_messages=flagged_messages,
            unflagged_messages=unflagged_messages,
            rules=rules,
            queries=queries,
            verbose=verbose)


def mdm_formatter(results, verbose):
    """Convert Message Data Model into human-readable text."""
    gron_output = gron.gron(json.dumps(results))
    gron_output = gron_output.replace('json = {}', 'message_data_model = {}')
    gron_output = re.sub(r'\njson\.', '\n', gron_output)

    return gron_output

    # template = JINJA2_ENV.get_template("message_data_model.txt.j2")
    # return template.render(results=results, verbose=verbose)


def format_mql(mql, offset=0):
    mql = mql.replace("&&", "\n  &&")
    mql = mql.replace("||", "\n  ||")
    mql = mql.replace("],", "],\n  ")
    mql = mql.replace("\n", "\n" + "  "*offset)
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
