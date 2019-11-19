"""CLI subcommands."""

import platform

import click

from sublime.__version__ import __version__
from sublime.cli.decorator import (
    enrich_command,
    analyze_command,
    not_implemented_command,
)
from sublime.cli.helper import *
from sublime.util import CONFIG_FILE, DEFAULT_CONFIG, save_config


'''
@not_implemented_command
def feedback():
    """Send feedback directly to the Sublime team."""
'''


@click.command(name="help")
@click.pass_context
def help_(context):
    """Show this message and exit."""
    click.echo(context.parent.get_help())


@enrich_command
@click.option("-v", "--verbose", count=True, help="Verbose output")
def enrich(
    context,
    api_client,
    api_key,
    input_file,
    output_file,
    output_format,
    verbose,
):
    """Enrich an EML."""
    # emls = load emls from input directory
    # results = [api_client.enrich(eml=input_file) for ip_address in ip_addresses]
    eml = load_eml_as_base64(context, input_file)
    results = api_client.enrich_eml(eml=eml)
    return results
    # return results["message_data_model"]


@analyze_command
@click.option("-v", "--verbose", count=True, help="Verbose output")
def analyze(
    context,
    api_client,
    api_key,
    input_file,
    detections_file,
    detection_query,
    output_file,
    output_format,
    verbose,
):
    """Analyze an enriched MDM or raw EML."""
    # assume it's an EML if it does not end with .mdm
    if input_file.name.endswith(".mdm"):
        message_data_model = load_message_data_model(context, input_file)
    else:
        eml = load_eml_as_base64(context, input_file)
        result = api_client.enrich_eml(eml=eml)
        message_data_model = result['message_data_model']

    if detections_file:
        detections = load_detections(context, detections_file)
        results = api_client.analyze_mdm_multi(message_data_model, detections, verbose)
    else:
        detection = create_detection(detection_query)
        results = api_client.analyze_mdm(message_data_model, detection, verbose)
        
    return results


@click.command()
@click.option("-k", "--api-key", required=True, help="Key to include in API requests")
def setup(api_key):
    """Configure API key."""
    config = {"api_key": api_key}
    save_config(config)
    click.echo("Configuration saved to {!r}".format(CONFIG_FILE))


@click.command()
def version():
    """Get version and OS information for your Sublime commandline installation."""
    click.echo(
        "sublime {}\n"
        "  Python {}\n"
        "  {}\n".format(__version__, platform.python_version(), platform.platform())
    )
