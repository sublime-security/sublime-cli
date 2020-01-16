"""Helper functions to reduce subcommand duplication."""

import sys
import email
import base64
import json
from pathlib import Path

import click
import structlog

LOGGER = structlog.get_logger()

def load_eml_as_base64(context, input_file):
    if input_file is None:
        click.echo(context.get_help())
        context.exit(-1)

    try:
        message = email.message_from_file(input_file)
        decoded = base64.urlsafe_b64encode(message.as_string().encode('utf-8')).decode('ascii')

        # fails for utf-8 messages:
        # decoded = base64.b64encode(message.as_bytes()).decode('ascii') 
    except Exception as exception:
        error_message = "Could not load EML: {}".format(exception)
        LOGGER.error(error_message)
        context.exit(-1)

    return decoded


def load_message_data_model(context, input_file):
    if input_file is None:
        click.echo(context.get_help())
        context.exit(-1)
    
    try:
        message_data_model = json.load(input_file)
    except Exception as exception:
        error_message = "Could not load MDM: {}".format(exception)
        LOGGER.error(error_message)
        context.exit(-1)

    return message_data_model


# this function is used for both loading detections and queries
def load_detections_path(context, detections_path, query=False):
    detections = []
    for detections_file in Path(detections_path).rglob("*.pql"):
        with detections_file.open() as f:
            detections.extend(load_detections(context, f, query))

    return detections

# this function is used for both loading detections and queries
def load_detections(context, detections_file, query=False):
    if detections_file is None:
        click.echo(context.get_help())
        context.exit(-1)

    # detections can span multiple lines, separated by an extra \n
    detections = []
    detection_str = ""
    detection_name = ""
    line = detections_file.readline()
    while line:
        line = line.strip("\n") # remove trailing newline
        line = line.strip() # remove leading/trailing whitespace

        if line.startswith("#"): # remove comments
            line = detections_file.readline()
            continue

        if line.startswith(";"): # detection names
            line = line.strip(";")
            line = line.strip() # remove leading/trailing whitespace
            detection_name = line
            line = detections_file.readline()
            continue

        if not line:
            # reached the end of a detection
            if detection_str:
                if not query:
                    detection = create_detection(detection_str, detection_name)
                else:
                    detection = create_query(detection_str, detection_name)
                detections.append(detection)
                detection_str = ""
                detection_name = ""
            # reached a line with just whitespace
            else:
                line = detections_file.readline()
                continue
        else:
            # append multi-line detections
            detection_str += " " + line + " "

        line = detections_file.readline()

    # true if there's no newline at the end of the last detection
    if detection_str:
        if not query:
            detection = create_detection(detection_str, detection_name)
        else:
            detection = create_query(detection_str, detection_name)
        detections.append(detection)
        detection_str = ""
        detection_name = ""

    if not detections:
        click.echo("No detections/queries found in PQL file")
        context.exit(-1)

    return detections

def create_detection(detection_str, detection_name=None):
    detection_str = detection_str.strip() if detection_str else None
    detection_name = detection_name.strip() if detection_name else None

    detection = { 
            "detection": detection_str,
            "name": detection_name
    }

    return detection

def create_query(query_str, query_name=None):
    query_str = query_str.strip() if query_str else None
    query_name = query_name.strip() if query_name else None

    query = {
            "query": query_str,
            "name": query_name
    }

    return query

def get_datetime_formats():
    formats=[
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f%z',
            '%Y-%m-%d %H:%M:%S'
    ]

    return formats
