"""Helper functions to reduce subcommand duplication."""

import sys
import email
import base64
import json

import click

def load_eml_as_base64(context, input_file):
    if input_file is None:
        click.echo(context.get_help())
        context.exit(-1)

    message = email.message_from_file(input_file)
    return base64.b64encode(message.as_string().encode('utf-8')).decode('ascii')
    # return base64.b64encode(message.as_bytes()).decode('ascii') # doesn't work for utf-8 messages


def load_message_data_model(context, input_file):
    if input_file is None:
        click.echo(context.get_help())
        context.exit(-1)
    
    message_data_model = json.load(input_file)
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

def create_detection(query):
    detection = { 
            "query": query.strip()
    }

    return detection
