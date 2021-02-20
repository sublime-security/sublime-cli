"""Sublime API client."""

import os
import json
import datetime
from collections import OrderedDict

import more_itertools
import requests
import structlog

from sublime.__version__ import __version__
from sublime.error import RateLimitError, InvalidRequestError, APIError, AuthenticationError
from sublime.util import load_config

LOGGER = structlog.get_logger()


class Sublime(object):

    """Sublime API client.

    :param api_key: Key used to access the API.
    :type api_key: str

    """

    _NAME = "Sublime"
    _BASE_URL = os.environ.get('BASE_URL')
    _BASE_URL = _BASE_URL if _BASE_URL else "https://alpha.api.sublimesecurity.com"
    _API_VERSION = "v1"
    _EP_ME = "me"
    _EP_FEEDBACK = "feedback"
    _EP_MESSAGES_CREATE = "messages"
    _EP_MESSAGES_ANALYZE = "messages/analyze"
    _EP_RAW_MESSAGES_ANALYZE = "raw-messages/analyze"
    _EP_NOT_IMPLEMENTED = "request/{subcommand}"

    def __init__(self, api_key=None):
        if api_key is None:
            config = load_config()
            api_key = config.get("api_key")

        self._api_key = api_key
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
        :raises InvalidRequestError: when HTTP status code is 400 or 404
        :raises RateLimitError: when HTTP status code is 429
        :raises APIError: for all other 4xx or 5xx status codes

        """
        if params is None:
            params = {}
        headers = {
            "User-Agent": "sublime-cli/{}".format(__version__)
        }
        if self._api_key:
            headers["Key"] = self._api_key
        url = "/".join([self._BASE_URL, self._API_VERSION, endpoint])

        # LOGGER.debug("Sending API request...", url=url, params=params, json=json)

        if request_type == 'GET':
            response = self.session.get(
                url, headers=headers, params=params, json=json
            )
        elif request_type == 'POST':
            response = self.session.post(
                    url, headers=headers, json=json
            )
        elif request_type == 'PATCH':
            response = self.session.patch(
                    url, headers=headers, json=json
            )
        elif request_type == 'DELETE':
            response = self.session.delete(
                    url, headers=headers, params=params
            )
        else:
            raise Exception("not implemented")


        if "application/json" in response.headers.get("Content-Type", ""):
            # 204 has no content and will trigger an exception
            if response.status_code != 204:
                body = response.json()
            else:
                body = None
        else:
            body = response.text

        if response.status_code >= 400:
            self._handle_error_response(response, body)

        return body, response.headers

    def _handle_error_response(self, resp, resp_body):
        try:
            error_data = resp_body["error"]
            message = error_data["message"]
        except:
            raise APIError(
                    "Invalid response from API: %r (HTTP response code "
                    "was %d)" % (resp_body, resp.status_code),
                    status_code=resp.status_code,
                    headers=resp.headers)

        if resp.status_code in [400, 404]:
            err = InvalidRequestError(
                    message=message,
                    status_code=resp.status_code,
                    headers=resp.headers)
        elif resp.status_code == 401:
            err = AuthenticationError(
                    message=message,
                    status_code=resp.status_code,
                    headers=resp.headers)
        elif resp.status_code == 429:
            err = RateLimitError(
                    message=message,
                    status_code=resp.status_code,
                    headers=resp.headers)
        else:
            err = APIError(
                    message=message,
                    status_code=resp.status_code,
                    headers=resp.headers)

        raise err

    def me(self):
        """Get information about the currently authenticated Sublime user."""

        endpoint = self._EP_ME
        response, _ = self._request(endpoint, request_type='GET')
        return response

    def create_message(self, raw_message, mailbox_email_address=None, message_type=None):
        """Create a Message Data Model from a raw message.

        :param raw_message: Base64 encoded raw message
        :type raw_message: str
        :param mailbox_email_address: Email address of the mailbox
        :type mailbox_email_address: str
        :param message_type: The type of message from the perspective of your organization (inbound, internal, outbound)
        :type message_type: str
        :rtype: dict
        
        """

        # LOGGER.debug("Creating a message data model...")

        body = {}
        body["raw_message"] = raw_message

        if mailbox_email_address:
            body["mailbox_email_address"] = mailbox_email_address
        if message_type:
            body["message_type"] = message_type

        endpoint = self._EP_MESSAGES_CREATE
        response, _ = self._request(endpoint, request_type='POST', json=body)
        return response

    def analyze_message(self, message_data_model, rules, queries):
        """Analyze a Message Data Model against a list of rules or queries.

        :param message_data_model: Message Data Model
        :type message_data_model: dict
        :param rules: Rules to run
        :type rules: list
        :param queries: Queries to run
        :type queries: list
        :rtype: dict

        """
        
        # LOGGER.debug("Analyzing message data model...")

        body = {}
        body["data_model"] = message_data_model
        body["rules"] = rules
        body["queries"] = queries

        endpoint = self._EP_MESSAGES_ANALYZE
        response, _ = self._request(endpoint, request_type='POST', json=body)
        return response

    def analyze_raw_message(self, raw_message, rules, queries, mailbox_email_address=None, message_type=None):
        """Analyze a raw message against a list of rules or queries.

        :param raw_message: Base64 encoded raw message
        :type raw_message: str
        :param rules: Rules to run
        :type rules: list
        :param queries: Queries to run
        :type queries: list
        :param mailbox_email_address: Email address of the mailbox
        :type mailbox_email_address: str
        :param message_type: The type of message from the perspective of your organization (inbound, internal, outbound)
        :type message_type: str
        :rtype: dict

        """

        # LOGGER.debug("Analyzing raw message...")

        body = {}
        body["raw_message"] = raw_message

        if mailbox_email_address:
            body["mailbox_email_address"] = mailbox_email_address
        if message_type:
            body["message_type"] = message_type

        body["rules"] = rules
        body["queries"] = queries

        endpoint = self._EP_RAW_MESSAGES_ANALYZE
        response, _ = self._request(endpoint, request_type='POST', json=body)
        return response

    def feedback(self, feedback):
        """Send feedback directly to the Sublime team.

        :param feedback: Feedback
        :type feedback: str
        :rtype: dict

        """

        # LOGGER.debug("Sending feedback...")

        body = {}
        body["feedback"] = feedback 

        endpoint = self._EP_FEEDBACK
        response, _ = self._request(endpoint, request_type='POST', json=body)
        return response


    def _not_implemented(self, subcommand_name):
        """Send request for a not implemented CLI subcommand.

        :param subcommand_name: Name of the CLI subcommand
        :type subcommand_name: str

        """
        endpoint = self._EP_NOT_IMPLEMENTED.format(subcommand=subcommand_name)
        response, _ = self._request(endpoint)
        return response


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)
