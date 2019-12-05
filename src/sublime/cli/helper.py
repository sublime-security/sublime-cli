"""Helper functions to reduce subcommand duplication."""

import sys
import email
import base64
import json

import click
import structlog

LOGGER = structlog.get_logger()

def load_eml_as_base64(context, input_file):
    if input_file is None:
        click.echo(context.get_help())
        context.exit(-1)

    try:
        message = email.message_from_file(input_file)
        decoded = base64.b64encode(message.as_string().encode('utf-8')).decode('ascii')
    except Exception as exception:
        error_message = "Could not load EML: {}".format(exception)
        LOGGER.error(error_message)
        context.exit(-1)

    return decoded

    # doesn't work for utf-8 messages
    # return base64.b64encode(message.as_bytes()).decode('ascii') 


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


def load_detections(context, detections_file):
    if detections_file is None:
        click.echo(context.get_help())
        context.exit(-1)

    # detections can span multiple lines, separated by an extra \n
    detections = []
    detection_str = ""
    line = detections_file.readline()
    while line:
        line = line.strip('\n') # remove trailing newline
        line = line.strip() # remove leading/trailing whitespace
        if line.startswith('#'): # remove comments
            line = detections_file.readline()
            continue

        if not line:
            # reached the end of a detection
            if detection_str:
                detection = create_detection(detection_str)
                detections.append(detection)
                detection_str = ""
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
        detection = create_detection(detection_str)
        detections.append(detection)
        detection_str = ""

    if not detections:
        click.echo("No detections found in detections file")
        context.exit(-1)

    return detections

def create_detection(detection_str):
    detection = { 
            "detection": detection_str.strip()
    }

    return detection

def create_query(query_str):
    query = {
            "query": query_str.strip()
    }

    return query
