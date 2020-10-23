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
        "detection": ansimarkup.parse("<white>"),
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


def json_formatter(result, verbose):
    """Format result as json."""
    return json.dumps(result, indent=4)


@colored_output
def enrich_details_formatter(result, verbose):
    template = JINJA2_ENV.get_template("enrich_details.txt.j2")
    total_enrichments = len(result["details"])
    success_enrichments = len([True for detail in result["details"] if detail["success"]])
    return template.render(details=result["details"], 
            total=total_enrichments, successful=success_enrichments, verbose=verbose)


@colored_output
def analyze_formatter(results, verbose):
    """Convert Analyze output into human-readable text."""
    template = JINJA2_ENV.get_template("analyze_result.txt.j2")

    # analyze/multi will return 'results', otherwise 'result'
    results = results["results"] if "results" in results else [results["result"]]

    for result in results:
        if result["detection"]:
            result["detection"] = format_detection(result["detection"])

    return template.render(results=results, verbose=verbose)


@colored_output
def query_formatter(results, verbose, show_all):
    """Convert Query output into human-readable text."""
    template = JINJA2_ENV.get_template("query_result.txt.j2")

    results = results["results"] if "results" in results else [results["result"]]
    for result in results:
        if result["type"] in ("list", "dict"):
            result["result"] = json_formatter(json.loads(result["result"]), False)

        if result["query"]:
            result["query"] = format_detection(result["query"])

    return template.render(results=results, verbose=verbose, show_all=show_all)


def mdm_formatter(results, verbose):
    """Convert Message Data Model into human-readable text."""
    gron_output = gron.gron(json.dumps(results))
    gron_output = gron_output.replace('json = {}', 'message_data_model = {}')
    gron_output = re.sub(r'\njson\.', '\n', gron_output)

    return gron_output

    # template = JINJA2_ENV.get_template("message_data_model.txt.j2")
    # return template.render(results=results, verbose=verbose)

@colored_output
def create_detections_formatter(results, verbose):
    """Convert detections creation output into human-readable text."""
    template = JINJA2_ENV.get_template("create_detections_result.txt.j2")

    return template.render(
            success_results=results["success"], 
            fail_results=results["fail"],
            verbose=verbose)

def format_detection(detection):
    detection = detection.replace("&&", "\n  &&")
    detection = detection.replace("||", "\n  ||")
    detection = detection.replace("],", "],\n  ")

    return detection

@colored_output
def get_detections_formatter(results, verbose):
    """Convert get detections output into human-readable text."""
    template = JINJA2_ENV.get_template("get_detections_result.txt.j2")

    # calculate the max widths of various columns to align them in output
    max_name_width = 0
    max_user_org_width = 0
    for result in results["detections"]:
        cur_name_width = 0
        cur_user_org_width = 0

        if result["name"]:
            cur_name_width = len(result["name"])
            if cur_name_width > max_name_width:
                max_name_width = cur_name_width

        if result["detection"]:
            result["detection"] = format_detection(result["detection"])

        result["created_by_author"] = "({}, {})".format(
                result.get("created_by_sublime_user_full_name"),
                result.get("created_by_org_name"))

        cur_user_org_width = len(result["created_by_author"])
        if cur_user_org_width > max_user_org_width:
            max_user_org_width = cur_user_org_width

    return template.render(results=results["detections"],
            name_width=max_name_width,
            user_org_width=max_user_org_width,
            verbose=verbose)

@colored_output
def get_messages_formatter(results, verbose):
    """Convert get messages output into human-readable text."""

    if results.get("message_data_model"): # GET /messages/{id}
        template = JINJA2_ENV.get_template("get_messages_detail.txt.j2")

        if results.get("enrichment_results"):
            total_enrichments = len(results["enrichment_results"]["details"])
            total_successful_enrichments = len([True for detail in
                results["enrichment_results"]["details"] if detail["success"]])
            enrichment_details = results["enrichment_results"]["details"]
        else:
            total_enrichments = 0
            total_successful_enrichments = 0
            enrichment_details = []

        for result in results["detection_results"]:
            result["detection"] = format_detection(result["detection"])

        return template.render(
            created_at=results["created_at"],
            detection_results=results["detection_results"],
            enrichment_details=enrichment_details,
            id=results["id"],
            mailbox_email_address=results["mailbox_email_address"],
            sender_display_name=results["sender_display_name"],
            sender_email_address=results["sender_email_address"],
            spam_folder=results["spam_folder"],
            subject=results["subject"],
            total_enrichments=total_enrichments,
            total_successful_enrichments=total_successful_enrichments,
            verbose=verbose)
    else: # GET /messages
        template = JINJA2_ENV.get_template("get_messages_result.txt.j2")

        # reverse results so the most recent message is shown last
        # (which is the first result the user sees at the end of the list)
        results["results"].reverse()

        return template.render(results=results["results"], verbose=verbose)

@colored_output
def update_detections_formatter(results, verbose):
    """Convert update detections output into human-readable text."""

    template = JINJA2_ENV.get_template("update_detections_result.txt.j2")
    return template.render(
            success_results=results["success"], 
            fail_results=results["fail"],
            verbose=verbose)

@colored_output
def update_messages_formatter(results, verbose):
    """Convert update messages output into human-readable text."""

    results = results["results"] if "results" in results else [results["result"]]
    template = JINJA2_ENV.get_template("update_messages_result.txt.j2")
    return template.render(results=results, verbose=verbose)

@colored_output
def get_me_formatter(result, verbose):
    """Convert 'get me' output into human-readable text."""
    template = JINJA2_ENV.get_template("get_me_result.txt.j2")

    return template.render(result=result, verbose=verbose)

@colored_output
def get_org_formatter(result, verbose):
    """Convert 'get org' output into human-readable text."""
    template = JINJA2_ENV.get_template("get_org_result.txt.j2")

    return template.render(result=result, verbose=verbose)

@colored_output
def listen_formatter(result, verbose):
    """Convert listen output into human-readable text."""
    template = JINJA2_ENV.get_template("listen_result.txt.j2")

    return template.render(result=result, verbose=verbose)

@colored_output
def send_mock_formatter(result, verbose):
    """Convert send mock output into human-readable text."""
    template = JINJA2_ENV.get_template("send_mock_result.txt.j2")

    return template.render(result=result, verbose=verbose)

@colored_output
def update_users_formatter(results, verbose):
    """Convert update users output into human-readable text."""
    template = JINJA2_ENV.get_template("update_users_result.txt.j2")

    return template.render(
            success_results=results["success"],
            fail_results=results["fail"],
            verbose=verbose)

@colored_output
def get_users_formatter(results, verbose):
    """Convert get users output into human-readable text."""
    template = JINJA2_ENV.get_template("get_users_result.txt.j2")

    return template.render(results=results["users"], verbose=verbose)

@colored_output
def backtest_detections_formatter(results, verbose):
    """Convert backtest detections output into human-readable text."""
    template = JINJA2_ENV.get_template("backtest_detections_results.txt.j2")

    return template.render(
            detections=results["detections"],
            results=results["results"], 
            total_messages_flagged=results["total_messages_flagged"],
            total_messages_analyzed=results["total_messages_analyzed"],
            total_new_messages_flagged=results["total_new_messages_flagged"],
            verbose=verbose)

@colored_output
def delete_messages_formatter(results, verbose):
    """Convert delete external message output into human-readable text."""
    template = JINJA2_ENV.get_template("delete_messages_result.txt.j2")

    return template.render(results=results, verbose=verbose)

@colored_output
def subscribe_detections_formatter(results, verbose):
    """Convert subscribe detections output into human-readable text."""
    template = JINJA2_ENV.get_template("subscribe_detections_result.txt.j2")

    return template.render(
            success_results=results["success"], 
            fail_results=results["fail"],
            verbose=verbose)

@colored_output
def share_detections_formatter(results, verbose):
    """Convert share detections output into human-readable text."""
    template = JINJA2_ENV.get_template("share_detections_result.txt.j2")

    return template.render(results=results, verbose=verbose)


FORMATTERS = {
    "json": json_formatter,
    "txt": {
        "enrich": mdm_formatter,
        "create": mdm_formatter,
        "analyze": analyze_formatter,
        "enrich_details": enrich_details_formatter,
        "query": query_formatter,
        "create_detections": create_detections_formatter,
        "get_detections": get_detections_formatter,
        "get_messages": get_messages_formatter,
        "update_detections": update_detections_formatter,
        "get_me": get_me_formatter,
        "get_org": get_org_formatter,
        "update_messages": update_messages_formatter,
        "listen": listen_formatter,
        "send_mock": send_mock_formatter,
        "update_users": update_users_formatter,
        "get_users": get_users_formatter,
        "backtest_detections": backtest_detections_formatter,
        "delete_messages": delete_messages_formatter,
        "subscribe_detections": subscribe_detections_formatter,
        "share_detections": share_detections_formatter
    },
}
