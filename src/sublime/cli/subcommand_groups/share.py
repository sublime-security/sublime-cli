"""CLI share subcommands."""

import os
import platform

import click

from sublime.__version__ import __version__
from sublime.cli.decorator import (
    echo_result,
    handle_exceptions,
    pass_api_client,
    MissingDetectionInput
)
from sublime.cli.helper import *


@click.group()
def share():
    """Share or unshare items in the Sublime community."""
    pass

@share.command()
@click.option("-v", "--verbose", count=True, help="Verbose output")
@click.option("-k", "--api-key", help="Key to include in API requests")
@click.option("-i", "--id", "detection_id",
        help="Detection ID to share")
@click.option("-n", "--name", "detection_name",
        help="Detection name to share")
@click.option("--share-name", "share_sublime_user", default="false", show_default=True,
        type=click.Choice(['true', 'false'], case_sensitive=False),
        help="Share your name with the community")
@click.option("--share-org", "share_org", default="false", show_default=True, 
        type=click.Choice(['true', 'false'], case_sensitive=False),
        help="Share your org name with the community")
@click.option("-u", "--unshare", "unshare", is_flag=True,
        help="Unshare the detection")
@click.option(
    "-o", "--output", "output_file", type=click.File(mode="w"), 
    help="Output file"
)
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["json", "txt"]),
    default="txt",
    help="Output format",
)
@pass_api_client
@click.pass_context
@echo_result
@handle_exceptions
def detections(
    context,
    api_client,
    api_key,
    detection_id,
    detection_name,
    share_sublime_user,
    share_org,
    unshare,
    output_file,
    output_format,
    verbose,
):
    """Share or unshare detections."""

    if detection_id:
        if unshare:
            result = api_client.get_org_detection_stats(detection_id)

            if result["subscribers"] > 0:
                if result["subscribers"] > 1:
                    message = (
                            "There are currently {} organizations subscribed "
                            "to this detection. Are you sure you want to unshare it?" 
                            .format(result["subscribers"])
                    )
                else:
                    message = (
                            "There is currently 1 organization subscribed "
                            "to this detection. Are you sure you want to unshare it?" 
                    )
                if click.confirm(message, abort=False):
                    results = [api_client.unshare_org_detection(detection_id)]
                else:
                    click.echo("Aborted!")
                    context.exit(-1)
        else:
            results = [api_client.share_org_detection(detection_id, 
                    share_sublime_user, share_org)]
    elif detection_name:
        if unshare:
            result = api_client.get_org_detection_stats_by_name(detection_name)

            if result["subscribers"] > 0:
                if result["subscribers"] > 1:
                    message = (
                            "There are currently {} organizations subscribed "
                            "to this detection. Are you sure you want to unshare it?" 
                            .format(result["subscribers"])
                    )
                else:
                    message = (
                            "There is currently 1 organization subscribed "
                            "to this detection. Are you sure you want to unshare it?" 
                    )
                if click.confirm(message, abort=False):
                    results = [api_client.unshare_org_detection_by_name(detection_name)]
                else:
                    click.echo("Aborted!")
                    context.exit(-1)
        else:
            results = [api_client.share_org_detection_by_name(detection_name, 
                    share_sublime_user, share_org)]
    else:
        LOGGER.error("Missing detection ID or name")
        context.exit(-1)

    return results
