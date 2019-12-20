"""Sublime API client."""

import os
from collections import OrderedDict

import more_itertools
import requests
import structlog
from halo import Halo

from sublime.__version__ import __version__
from sublime.exceptions import RateLimitError, RequestFailure
from sublime.util import load_config

LOGGER = structlog.get_logger()


class Sublime(object):

    """Sublime API client.

    :param api_key: Key used to access the API.
    :type api_key: str

    """

    NAME = "Sublime"
    BASE_URL = os.environ.get('BASE_URL')
    BASE_URL = BASE_URL if BASE_URL else "https://api.sublimesecurity.com"
    API_VERSION = "v1"
    EP_MESSAGE_ANALYZE = "message/analyze"
    EP_MESSAGE_ANALYZE_MULTI = "message/analyze/multi"
    EP_MESSAGE_ENRICH = "message/enrich"
    EP_MESSAGE_CREATE = "message/create"
    EP_MODEL_ANALYZE = "model/analyze"
    EP_MODEL_QUERY = "model/query"
    EP_MODEL_ANALYZE_MULTI = "model/analyze/multi"
    EP_DETECTIONS = "org/detections/"
    EP_NOT_IMPLEMENTED = "request/{subcommand}"

    def __init__(self, api_key=None, use_cache=True):
        if api_key is None:
            config = load_config()
            if api_key is None:
                api_key = config["api_key"]
        self.api_key = api_key
        self.use_cache = use_cache
        self.session = requests.Session()

    def _request(self, endpoint, request_type='GET', params=None, json=None):
        """Handle the requesting of information from the API.

        :param endpoint: Endpoint to send the request to.
        :type endpoint: str
        :param params: Request parameters.
        :type param: dict
        :param json: Request's JSON payload.
        :type json: dict
        :returns: Response's JSON payload
        :rtype: dict
        :raises RequestFailure: when HTTP status code is not 2xx

        """
        if params is None:
            params = {}
        headers = {
            "User-Agent": "Sublime/{}".format(__version__),
            "Key": self.api_key,
        }
        url = "/".join([self.BASE_URL, self.API_VERSION, endpoint])
        LOGGER.debug("Sending API request...", url=url, params=params, json=json)

        if request_type == 'GET':
            response = self.session.get(
                url, headers=headers, params=params, json=json
            )
        elif request_type == 'POST':
            response = self.session.post(
                    url, headers=headers, json=json
            )
        else:
            raise Exception("not implemented")


        if "application/json" in response.headers.get("Content-Type", ""):
            body = response.json()
        else:
            body = response.text

        if response.status_code == 429:
            raise RateLimitError(body)
        if response.status_code >= 400:
            raise RequestFailure(response.status_code, body)

        return body

    def analyze_mdm_multi(self, message_data_model, detections, verbose):
        """Analyze an enriched Message Data Model against a list of detections"""

        body = {}
        body["message_data_model"] = message_data_model
        body["detections"] = detections
        if verbose:
            body["response_type"] = "full"
        endpoint = self.EP_MODEL_ANALYZE_MULTI
        response = self._request(endpoint, request_type='POST', json=body)
        return response

    def analyze_mdm(self, message_data_model, detection, verbose):
        """Analyze an enriched Message Data Model against a detection"""
        body = {}
        body["message_data_model"] = message_data_model
        body["detection"] = detection
        if verbose:
            body["response_type"] = "full"
        endpoint = self.EP_MODEL_ANALYZE
        response = self._request(endpoint, request_type='POST', json=body)
        return response

    def query_mdm(self, message_data_model, query, verbose):
        """Query an enriched Message Data Model"""
        body = {}
        body["message_data_model"] = message_data_model
        body["query"] = query
        if verbose:
            body["response_type"] = "full"
        endpoint = self.EP_MODEL_QUERY
        response = self._request(endpoint, request_type='POST', json=body)
        return response

    def create_mdm(self, eml):
        """Create an unenriched MDM from an EML.

        :param eml: Raw EML to enrich.
        :type eml: str
        :return: Unenriched Message Data Model.
        :rtype: dict

        """

        LOGGER.debug("Creating an unenriched MDM...")

        body = {}
        body["message"] = eml
        endpoint = self.EP_MESSAGE_CREATE
        response = self._request(endpoint, request_type='POST', json=body)
        return response

    def enrich_eml(self, eml):
        """Enrich an EML.

        :param eml: Raw EML to enrich.
        :type eml: str
        :return: Enriched Message Data Model.
        :rtype: dict

        """

        LOGGER.debug("Creating MDM and enriching from EML...")

        body = {}
        body["message"] = eml
        endpoint = self.EP_MESSAGE_ENRICH
        with Halo(text='Enriching', spinner='dots'):
            response = self._request(endpoint, request_type='POST', json=body)
        return response

    def analyze_eml(self, eml, detection, verbose):
        """Analyze an EML against a detection."""

        LOGGER.debug("Analyzing EML...")

        body = {}
        body["message"] = eml
        body["detection"] = detection
        endpoint = self.EP_MESSAGE_ANALYZE
        with Halo(text='Enriching and analyzing', spinner='dots'):
            response = self._request(endpoint, request_type='POST', json=body)
        return response

    def analyze_eml_multi(self, eml, detections, verbose):
        """Analyze an EML against a list of detections."""

        LOGGER.debug("Analyzing EML...")

        body = {}
        body["message"] = eml
        body["detections"] = detections
        if verbose:
            body["response_type"] = "full"
        endpoint = self.EP_MESSAGE_ANALYZE_MULTI
        with Halo(text='Enriching and analyzing', spinner='dots'):
            response = self._request(endpoint, request_type='POST', json=body)
        return response

    def create_detection(self, detection, active, verbose):
        """Create a detection."""
        body = {}
        body["detection"] = detection["detection"]
        body["name"] = detection["name"]
        body["active"] = active
        if verbose:
            body["response_type"] = "full"

        endpoint = self.EP_DETECTIONS
        response = self._request(endpoint, request_type='POST', json=body)
        return response

    def get_detections(self, active):
        """Get detections."""
        params = {}
        params["active"] = active

        endpoint = self.EP_DETECTIONS
        response = self._request(endpoint, request_type='GET', params=params)
        return response

    def not_implemented(self, subcommand_name):
        """Send request for a not implemented CLI subcommand.

        :param subcommand_name: Name of the CLI subcommand
        :type subcommand_name: str

        """
        endpoint = self.EP_NOT_IMPLEMENTED.format(subcommand=subcommand_name)
        response = self._request(endpoint)
        return response

