"""CLI subcommands."""

import os
import platform

import click
import structlog
from halo import Halo
from pathlib import Path

from sublime.__version__ import __version__
from sublime.cli.decorator import (
    me_command,
    feedback_command,
    analyze_command,
    create_command,
    not_implemented_command,
    MissingRuleInput
)
from sublime.util import *

# for the listen subcommand
import ssl
import asyncio
from functools import wraps
from sublime.cli.formatter import FORMATTERS 

LOGGER = structlog.get_logger()


@click.command(name="help")
@click.pass_context
def help_(context):
    """Show this message and exit."""
    click.echo(context.parent.get_help())

def clear():
    """Clear the console"""
    # check and make call for appropriate operating system
    os.system('clear' if os.name =='posix' else 'cls')


@create_command
@click.option("-v", "--verbose", count=True, help="Verbose output")
def create(
    context,
    api_client,
    api_key,
    input_file,
    message_type,
    output_file,
    output_format,
    mailbox_email_address,
    verbose,
):
    """Create a Message Data Model from an EML or MSG."""
    request_permission()

    if input_file.name.endswith(".msg"):
        raw_message = load_msg_file_handle(input_file)
    else:
        raw_message = load_eml_file_handle(input_file)

    results = api_client.create_message(
            raw_message,
            mailbox_email_address,
            message_type)

    return results


@analyze_command
@click.option("-v", "--verbose", count=True, help="Verbose output")
def analyze(
    context,
    api_client,
    api_key,
    input_path,
    run_path,
    query,
    message_type,
    mailbox_email_address,
    output_file,
    output_format,
    verbose,
):
    """Analyze a file or directory of EMLs, MSGs, or MDMs."""
    request_permission()

    if not run_path and not query:
        raise MissingRuleInput

    # load all rules and queries
    rules, queries = [], []
    if run_path:
        if os.path.isfile(run_path):
            with open(run_path, encoding='utf-8') as f:
                try:
                    rules, queries = load_yml(f)
                except LoadRuleError as error:
                    LOGGER.warning(error.message)

        elif os.path.isdir(run_path):
            rules, queries = load_yml_path(run_path)

    elif query:
        queries = [{
                "source": query,
                "name": None,
        }]

    if not rules and not queries:
        LOGGER.error("YML file or raw MQL required")
        context.exit(-1)

    # sort rules and queries in advance so we don't have to later
    # analyze endpoint should conserve the order in which they're submitted
    rules = sorted(rules, key=lambda i: i['name'].lower() if i.get('name') else '')
    queries = sorted(queries, key=lambda i: i['name'].lower() if i.get('name') else '')

    # aggregate all files we need to check 
    file_paths = []
    if os.path.isfile(input_path):
        file_paths.append(input_path)
    else:
        for file_path in Path(input_path).rglob('*.mdm'):
            file_paths.append(str(file_path))
        for file_path in Path(input_path).rglob('*.msg'):
            file_paths.append(str(file_path))
        for file_path in Path(input_path).rglob('*.eml'):
            file_paths.append(str(file_path))
        for file_path in Path(input_path).rglob('*.mbox'):
            file_paths.append(str(file_path))

    # analyze each file and aggregate all responses
    results = {}
    num_files = len(file_paths)
    for i in range(num_files):
        file_path = file_paths[i]
        file_dir, _, file_name = file_path.rpartition('/')
        _, _, extension = file_name.rpartition('.')

        with Halo(
            text=f'Analyzing file {i+1} of {num_files} ( {file_name} )...',
            spinner='dots'
        ):
            if file_path.endswith('.mdm'):
                message_data_model = load_message_data_model(file_path)
                response = api_client.analyze_message(
                        message_data_model,
                        rules,
                        queries)

            elif file_path.endswith('.msg'):
                raw_message = load_msg(file_path)
                response = api_client.analyze_raw_message(
                        raw_message, 
                        rules,
                        queries,
                        mailbox_email_address,
                        message_type)

            elif file_path.endswith('.eml'):
                raw_message = load_eml(file_path)
                response = api_client.analyze_raw_message(
                        raw_message, 
                        rules,
                        queries,
                        mailbox_email_address,
                        message_type)

            elif file_path.endswith('.mbox'):
                # in the mbox case we want to retrieve the response for each message
                # contained and provide a unique results key for each entry
                for subject_unique, raw_message in load_mbox(file_path).items():
                    response = api_client.analyze_raw_message(
                            raw_message, 
                            rules,
                            queries,
                            mailbox_email_address,
                            message_type)
                    response['file_name'] = file_name
                    response['extension'] = extension
                    response['directory'] = file_dir
                    response['subject'] = subject_unique
                    results[file_path+subject_unique] = response
                continue
                    
            else:
                LOGGER.error("Input file must have .eml, .msg, .mdm or .mbox extension")
                context.exit(-1)
            
            response['file_name'] = file_name
            response['extension'] = extension
            response['directory'] = file_dir
            results[file_path] = response
 
    return results


@me_command
@click.option("-v", "--verbose", count=True, help="Verbose output")
def me(
    context,
    api_client,
    api_key,
    output_file,
    output_format,
    verbose,
):
    """Get information about the currently authenticated Sublime user."""

    result = api_client.me()

    return result


@feedback_command
def feedback(
    context,
    api_client,
    feedback
):
    """Send feedback directly to the Sublime team.

    Use single quotes for 'FEEDBACK'
    """

    result = api_client.feedback(feedback)

    return result


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
