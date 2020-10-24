"""Helper functions to reduce subcommand duplication."""

import sys
import email
import base64
import json
from pathlib import Path

import click
import structlog
from sublime.error import *

LOGGER = structlog.get_logger()


def load_eml(input_file):
    """Load EML file.

    :param input_file: File handle.
    :type input_file: _io.TextIOWrapper
    :returns: Base64-encoded EML
    :rtype: string
    :raises: LoadEMLError

    """
    if input_file is None:
        raise LoadEMLError("Missing EML file")

    try:
        message = email.message_from_file(input_file)
        decoded = base64.urlsafe_b64encode(
                message.as_string().encode('utf-8')).decode('ascii')

        # fails for utf-8 messages:
        # decoded = base64.b64encode(message.as_bytes()).decode('ascii') 
    except Exception as exception:
        error_message = "{}".format(exception)
        raise LoadEMLError(error_message)

    return decoded


def load_message_data_model(input_file):
    """Load Message Data Model file.

    :param input_file: File handle.
    :type input_file: _io.TextIOWrapper
    :returns: Message Data Model JSON object
    :rtype: dict
    :raises: LoadMessageDataModelError

    """
    if input_file is None:
        raise LoadMessageDataModelError("Missing Message Data Model file")
    
    try:
        message_data_model = json.load(input_file)
    except Exception as exception:
        error_message = "{}".format(exception)
        raise LoadMessageDataModelError(error_message)

    return message_data_model

def load_detections_path(detections_path, query=False, ignore_errors=True):
    """Load detections or queries from a path.

    :param detections_path: Path to detections
    :type detections_path: string
    :param query: Whether the files contain queries opposed to detections
    :type query: boolean
    :param ignore_errors: Ignore detection loading errors
    :type query: boolean
    :returns: A list of detections or queries
    :rtype: list
    :raises: LoadDetectionError

    """
    detections = []
    for detections_file in Path(detections_path).rglob("*.pql"):
        with detections_file.open(encoding='utf-8') as f:
            try:
                detections.extend(load_detections(f, query, ignore_errors))
            except LoadDetectionError as error:
                # We want to ignore errors and continue reading the rest 
                # of the files. 
                if ignore_errors:
                    LOGGER.warning(error.message)
                else:
                    raise

    return detections

def load_detections(detections_file, query=False, ignore_errors=False):
    """Load detections or queries from a file.

    :param detections_file: Detections file
    :type detections_file: _io.TextIOWrapper
    :param query: Whether the file contains queries opposed to detections
    :type query: boolean
    :param ignore_errors: Ignore detection loading errors
    :type query: boolean
    :returns: A list of detections or queries
    :rtype: list
    :raises: LoadDetectionError

    """
    if detections_file is None:
        raise LoadDetectionError("Missing PQL file")

    # detections can span multiple lines, separated by an extra \n
    detections = []
    detection_str = ""
    detection_name = ""
    comment_exists = False
    line = detections_file.readline()
    while line:
        line = line.strip("\n") # remove trailing newline
        line = line.strip() # remove leading/trailing whitespace

        if line.startswith("#"): # remove comments
            line = detections_file.readline()
            comment_exists = True
            continue

        if line.startswith(";"): # detection names
            line = line.strip(";")
            line = line.strip() # remove leading/trailing whitespace
            detection_name = line
            line = detections_file.readline()
            continue

        # empty lines signify the end of a detection
        if not line:
            if detection_str:
                if query:
                    detection = create_query(detection_str, detection_name)
                else:
                    detection = create_simple_detection(
                            detection_str=detection_str,
                            detection_name=detection_name)
                detections.append(detection)
            elif detection_name:
                # reached a detection with just a name, no raw detection
                if comment_exists:
                    error = (
                            "This rule is commented out and may require "
                            "customization: '{}' in {}".format(
                                detection_name, detections_file.name)
                            )
                    if ignore_errors:
                        LOGGER.warning(error)
                    else:
                        raise LoadDetectionError(error)
                else:
                    error = (
                            "Missing detection: '{}' in {}'".format(
                                detection_name, detections_file.name)
                            )
                    if ignore_errors:
                        LOGGER.warning(error)
                    else:
                        raise LoadDetectionError(error)

            # reset variables
            detection_str = ""
            detection_name = ""
            comment_exists = False
        else:
            # append multi-line detections
            detection_str += " " + line + " "

        # advance to the next line
        line = detections_file.readline()

    # true if there's no newline at the end of the last detection
    if detection_str:
        if not query:
            detection = create_simple_detection(
                    detection_str=detection_str,
                    detection_name=detection_name)
        else:
            detection = create_query(detection_str, detection_name)
        detections.append(detection)
    elif detection_name:
        # reached a detection with just a name, no raw detection
        if comment_exists:
            error = (
                    "This rule is commented out and may require "
                    "customization: '{}' in {}".format(
                        detection_name, detections_file.name)
                    )
            if ignore_errors:
                LOGGER.warning(error)
            else:
                raise LoadDetectionError(error)

        else:
            error = (
                    "Missing detection: '{}' in {}'".format(
                        detection_name, detections_file.name)
                    )
            if ignore_errors:
                LOGGER.warning(error)
            else:
                raise LoadDetectionError(error)

    # did we load any valid detections?
    if not detections:
        if detection_name:
            error = (
                    "Missing detection: '{}' in {}'".format(
                        detection_name, detections_file.name)
                    )
            if ignore_errors:
                LOGGER.warning(error)
            else:
                raise LoadDetectionError(error)
        else:
            error = (
                    "No detections or queries found in '{}'".format(
                        detections_file.name)
                    )
            if ignore_errors:
                LOGGER.warning(error)
            else:
                raise LoadDetectionError(error)

    return detections

def create_simple_detection(
        detection_str=None,
        detection_name=None,
        detection_id=None):
    detection_str = detection_str.strip() if detection_str else None
    detection_name = detection_name.strip() if detection_name else None

    if not detection_str and not detection_name and not detection_id:
        LOGGER.error("Invalid detection")
        sys.exit(-1)

    detection = { 
            "detection": detection_str,
            "name": detection_name,
            "id": detection_id
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
