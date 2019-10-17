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
    detection_id = 1
    detection_str = ""
    line = detections_file.readline()
    while line:
        line = line.strip('\n')
        if line.startswith('#'):
            continue

        next_line = detections_file.readline()

        # we've reached an empty newline or EOF
        if not line or not next_line:
            # this should only trigger on the last detection
            detection_str = line if not detection_str else detection_str
            detection = { 
                    "detection_id": detection_id,
                    "query": detection_str
            }
            detections.append(detection)
            detection_id += 1
            detection_str = ""
        else:
            detection_str += " " + line + " "

        line = next_line

    if not detections:
        click.echo("No detections found in detections file")
        context.exit(-1)

    return detections
