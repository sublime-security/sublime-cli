"""CLI subcommands."""

import os
import platform

import click
import structlog
from halo import Halo

from sublime.__version__ import __version__
from sublime.cli.decorator import (
    enrich_command,
    analyze_command,
    query_command,
    generate_command,
    listen_command,
    not_implemented_command,
    MissingDetectionInput
)
from sublime.cli.helper import *
from sublime.util import CONFIG_FILE, DEFAULT_CONFIG, save_config

# for the listen subcommand
import ssl
import asyncio
import websockets
from functools import wraps
from sublime.cli.formatter import FORMATTERS 
from websockets.exceptions import InvalidStatusCode
from sublime.error import WebSocketError

LOGGER = structlog.get_logger()

'''
@not_implemented_command
def feedback():
    """Send feedback directly to the Sublime team."""
'''


# unused, not necessary
def asyncio_wrapper(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@click.command(name="help")
@click.pass_context
def help_(context):
    """Show this message and exit."""
    click.echo(context.parent.get_help())

def clear():
    """Clear the console"""
    # check and make call for appropriate operating system
    os.system('clear' if os.name =='posix' else 'cls')

@listen_command
@click.option("-v", "--verbose", count=True, help="Verbose output")
def listen(
    context,
    api_client,
    api_key,
    event_name,
    output_format,
    verbose,
):
    """Listen for real-time events occuring in your Sublime environment.

    Events: "flagged-messages"

    """

    # this is used for keeping track of all events still in the queue

    message_queue = []
    # we have to do the formatting here due to the nature of websockets
    formatter = FORMATTERS[output_format]
    formatter_name = "listen"
    if isinstance(formatter, dict):
        formatter = formatter[formatter_name]

    async def wsrun(uri):
        # if not in dev mode, force SSL over websocket
        if os.getenv('ENV') != 'local':
            ctx = ssl.create_default_context()
            ctx.verify_mode = ssl.CERT_REQUIRED
        else:
            ctx = None

        try:
            async with websockets.connect(uri, ssl=ctx) as websocket:
                await websocket.send('test')
                while True:
                    data = await websocket.recv()
                    try:
                        data = json.loads(data)
                        if "success" in data and not data["success"]:
                            raise WebSocketError(data["error"])
                    except ValueError:
                        pass

                    if isinstance(data, dict):
                        if data.get("event_name") == "flagged-messages-reviewed":
                            reviewed_id = data.get("message_data_model_id")

                            # loop through the queue and find/delete the MDM id
                            for i, message in enumerate(message_queue):
                                # ensure we're looking at a valid event
                                if isinstance(message, dict):
                                    cur_id = message.get("message_data_model_id")

                                    if cur_id == reviewed_id:
                                        del message_queue[i]
                        else:
                            message_queue.append(data)
                    else:
                        message_queue.append(data)

                    clear()

                    for item in message_queue:
                        output = formatter(item, verbose).strip("\n")

                        # file output doesn't work yet
                        click.echo(output, click.open_file("-", mode="w"))

        except InvalidStatusCode as e:
            # err = "Failed to establish connection."
            # raise WebSocketError(err)
            raise WebSocketError(e)
        except WebSocketError as e:
            raise
        except Exception as e:
            err = str(e)
            if "Connect call failed" in err:
                raise WebSocketError("Failed to establish connection")

            raise WebSocketError(e)

    api_key = api_client.api_key
    BASE_WEBSOCKET = os.environ.get('BASE_WEBSOCKET')
    BASE_WEBSOCKET = BASE_WEBSOCKET if BASE_WEBSOCKET else "wss://api.sublimesecurity.com"
    ws = f"{BASE_WEBSOCKET}/v1/org/listen/ws?api_key={api_key}&event_name={event_name}"

    asyncio.get_event_loop().run_until_complete(wsrun(ws))

    if output_file:
        click.echo(f"Output saved to {output_file}")


@enrich_command
@click.option("-v", "--verbose", count=True, help="Verbose output")
def enrich(
    context,
    api_client,
    api_key,
    input_file,
    output_file,
    output_format,
    mailbox_email_address,
    route_type,
    verbose,
):
    """Enrich an EML."""
    # emls = load emls from input directory
    # results = [api_client.enrich(eml=input_file) for ip_address in ip_addresses]
    eml = load_eml(input_file)
    with Halo(text='Enriching', spinner='dots'):
        results = api_client.enrich_eml(eml, mailbox_email_address, route_type)

    return results


@generate_command
@click.option("-v", "--verbose", count=True, help="Verbose output")
def generate(
    context,
    api_client,
    api_key,
    input_file,
    output_file,
    output_format,
    mailbox_email_address,
    verbose,
):
    """Generate an unenriched MDM from an EML."""
    # emls = load emls from input directory
    eml = load_eml(input_file)
    results = api_client.create_mdm(eml, mailbox_email_address)

    return results


@analyze_command
@click.option("-v", "--verbose", count=True, help="Verbose output")
def analyze(
    context,
    api_client,
    api_key,
    input_file,
    detections_path,
    detection_str,
    route_type,
    output_file,
    output_format,
    mailbox_email_address,
    verbose,
):
    """Analyze an enriched MDM or raw EML."""
    if not detections_path and not detection_str:
        raise MissingDetectionInput

    if detections_path:
        if os.path.isfile(detections_path):
            with open(detections_path, encoding='utf-8') as f:
                detections = load_detections(f)
                multi = True

        elif os.path.isdir(detections_path):
            detections = load_detections_path(detections_path)
            multi = True
    else:
        detection = create_detection(detection_str)
        multi = False

    # assume it's an EML if it doesn't end with .mdm
    if input_file.name.endswith(".mdm"):
        message_data_model = load_message_data_model(input_file)

        if multi:
            results = api_client.analyze_mdm_multi(
                    message_data_model, 
                    detections, 
                    verbose)
        else:
            results = api_client.analyze_mdm(
                    message_data_model, 
                    detection, 
                    verbose)
    else:
        eml = load_eml(input_file)

        with Halo(text='Enriching and analyzing', spinner='dots'):
            if multi:
                results = api_client.analyze_eml_multi(
                        eml, 
                        detections, 
                        mailbox_email_address,
                        route_type,
                        verbose)
            else:
                results = api_client.analyze_eml(
                        eml, 
                        detection, 
                        mailbox_email_address,
                        route_type,
                        verbose)

    if results.get("results"):
        results["results"] = sorted(results["results"], 
                key=lambda i: i["name"] if i.get("name") else "")

    return results


@query_command
@click.option("-v", "--verbose", count=True, help="Verbose output")
def query(
    context,
    api_client,
    api_key,
    input_file,
    show_all,
    query_path,
    query_str,
    output_file,
    output_format,
    verbose,
):
    """Query an enriched MDM and get the output."""
    if query_path:
        if os.path.isfile(query_path):
            with open(query_path, encoding='utf-8') as f:
                queries = load_detections(f, query=True)
                multi = True

        elif os.path.isdir(query_path):
            queries = load_detections_path(query_path, query=True)
            multi = True
    else:
        if not query_str:
            LOGGER.error("Query or PQL file(s) is required")
            context.exit(-1)

        query = create_query(query_str)
        multi = False

    message_data_model = load_message_data_model(input_file)

    if multi:
        results = api_client.query_mdm_multi(message_data_model, queries, verbose)
    else:
        results = api_client.query_mdm(message_data_model, query, verbose)

    '''
    if results.get("results"):
        results["results"] = sorted(results["results"], 
                key=lambda i: i["name"] if i.get("name") else "")
    '''

    return results


@click.command()
@click.option("-k", "--api-key", required=False, 
        help="Key to include in API requests")
@click.option("-s", "--save-dir", required=False,
        type=click.Path(resolve_path=True),
        help="Default save directory for items retrieved from your Sublime environment")
def setup(api_key="", save_dir=""):
    """Configure defaults."""
    config = {"api_key": api_key, "save_dir": save_dir}
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
