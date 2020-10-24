"""Sublime API client."""

import os
import json
import datetime
from collections import OrderedDict

import more_itertools
import requests
import structlog

from sublime.__version__ import __version__
from sublime.error import RateLimitError, InvalidRequestError, APIError
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
    EP_MODEL_ANALYZE_MULTI = "model/analyze/multi"
    EP_MODEL_QUERY = "model/query"
    EP_MODEL_QUERY_MULTI = "model/query/multi"
    EP_DETECTIONS = "detections"
    EP_ORG_DETECTIONS = "detections/org"
    EP_COMMUNITY_DETECTIONS = "detections/community"
    EP_DETECTION_BY_ID = "detections/{}"
    EP_DETECTION_BY_NAME = "detections/name/{}"
    EP_SUBSCRIBE_DETECTION_BY_ID = "detections/{}/subscribe"
    EP_UNSUBSCRIBE_DETECTION_BY_ID = "detections/{}/unsubscribe"
    EP_SHARE_DETECTION_BY_ID = "detections/{}/share"
    EP_UNSHARE_DETECTION_BY_ID = "detections/{}/unshare"
    EP_BACKTEST_DETECTIONS = "detections/backtest/multi"
    EP_GET_ME = "org/sublime-users/me"
    EP_GET_ORG = "org"
    EP_GET_USERS = "org/users"
    EP_FLAGGED_MESSAGES = "org/messages"
    EP_FLAGGED_MESSAGES_DETAIL = "org/messages/{}"
    EP_ADMIN_ACTION_REVIEW = "org/messages/{}/review"
    EP_ADMIN_ACTION_REVIEW_ALL = "org/messages/review/all"
    EP_ADMIN_ACTION_DELETE = "org/messages/{}/delete"
    EP_SEND_MOCK_TUTORIAL_ONE = "org/sublime-users/mock-tutorial-one"
    EP_ACTIVATE_USER = "org/users/email/{}/activate"
    EP_DEACTIVATE_USER = "org/users/email/{}/deactivate"
    EP_GET_JOB_STATUS = "jobs/{}/status"
    EP_GET_JOB_OUTPUT = "jobs/{}/output"
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
        :raises InvalidRequestError: when HTTP status code is 400 or 404
        :raises RateLimitError: when HTTP status code is 429
        :raises APIError: for all other 4xx or 5xx status codes

        """
        if params is None:
            params = {}
        headers = {
            "User-Agent": "sublime-cli/{}".format(__version__),
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
            self.handle_error_response(response, body)

        return body, response.headers

    def handle_error_response(self, resp, resp_body):
        try:
            error_data = resp_body["error"]
        except:
            raise APIError(
                    "Invalid response from API: %r (HTTP response code "
                    "was %d)" % (resp_body, resp.status_code),
                    status_code=resp.status_code,
                    headers=resp.headers)

        if resp.status_code in [400, 404]:
            err = InvalidRequestError(
                    message=error_data["message"],
                    status_code=resp.status_code,
                    headers=resp.headers)
        elif resp.status_code == 429:
            err = RateLimitError(
                    message=error_data["message"],
                    status_code=resp.status_code,
                    headers=resp.headers)
        else:
            err = APIError(
                    message=error_data["message"],
                    status_code=resp.status_code,
                    headers=resp.headers)

        raise err

    def analyze_mdm_multi(self, message_data_model, detections, verbose):
        """Analyze an enriched Message Data Model against a list of detections"""

        body = {}
        body["message_data_model"] = message_data_model
        body["detections"] = detections
        if verbose:
            body["response_type"] = "full"
        endpoint = self.EP_MODEL_ANALYZE_MULTI
        response, _ = self._request(endpoint, request_type='POST', json=body)
        return response

    def analyze_mdm(self, message_data_model, detection, verbose):
        """Analyze an enriched Message Data Model against a detection"""
        body = {}
        body["message_data_model"] = message_data_model
        body["detection"] = detection
        if verbose:
            body["response_type"] = "full"
        endpoint = self.EP_MODEL_ANALYZE
        response, _ = self._request(endpoint, request_type='POST', json=body)
        return response

    def query_mdm_multi(self, message_data_model, queries, verbose):
        """Query an enriched Message Data Model against a list of detections"""

        body = {}
        body["message_data_model"] = message_data_model
        body["queries"] = queries 
        if verbose:
            body["response_type"] = "full"
        endpoint = self.EP_MODEL_QUERY_MULTI
        response, _ = self._request(endpoint, request_type='POST', json=body)
        return response

    def query_mdm(self, message_data_model, query, verbose):
        """Query an enriched Message Data Model"""
        body = {}
        body["message_data_model"] = message_data_model
        body["query"] = query
        if verbose:
            body["response_type"] = "full"
        endpoint = self.EP_MODEL_QUERY
        response, _ = self._request(endpoint, request_type='POST', json=body)
        return response

    def create_mdm(self, eml, mailbox_email_address=None):
        """Create an unenriched MDM from an EML.

        :param eml: Raw EML to enrich.
        :type eml: str
        :return: Unenriched Message Data Model.
        :rtype: dict

        """

        LOGGER.debug("Creating an unenriched MDM...")

        body = {}
        body["message"] = eml
        body["mailbox_email_address"] = mailbox_email_address
        endpoint = self.EP_MESSAGE_CREATE
        response, _ = self._request(endpoint, request_type='POST', json=body)
        return response

    def enrich_eml(self, eml, mailbox_email_address=None, route_type=None):
        """Enrich an EML.

        :param eml: Raw EML to enrich.
        :type eml: str
        :return: Enriched Message Data Model.
        :rtype: dict

        """

        LOGGER.debug("Creating MDM and enriching from EML...")

        body = {}
        body["message"] = eml
        body["mailbox_email_address"] = mailbox_email_address
        body["route_type"] = route_type

        endpoint = self.EP_MESSAGE_ENRICH
        response, _ = self._request(endpoint, request_type='POST', json=body)
        return response

    def analyze_eml(self, eml, detection, mailbox_email_address, route_type, verbose):
        """Analyze an EML against a detection."""

        LOGGER.debug("Analyzing EML...")

        body = {}
        body["message"] = eml
        body["detection"] = detection
        body["mailbox_email_address"] = mailbox_email_address
        body["route_type"] = route_type
        if verbose:
            body["response_type"] = "full"

        endpoint = self.EP_MESSAGE_ANALYZE
        response, _ = self._request(endpoint, request_type='POST', json=body)
        return response

    def analyze_eml_multi(self, eml, detections, mailbox_email_address, 
            route_type, verbose):
        """Analyze an EML against a list of detections."""

        LOGGER.debug("Analyzing EML...")

        body = {}
        body["message"] = eml
        body["detections"] = detections
        body["mailbox_email_address"] = mailbox_email_address
        body["route_type"] = route_type
        if verbose:
            body["response_type"] = "full"

        endpoint = self.EP_MESSAGE_ANALYZE_MULTI
        response, _ = self._request(endpoint, request_type='POST', json=body)
        return response

    def get_detection(self, detection_id):
        """Get a detection by ID."""
        endpoint = self.EP_DETECTION_BY_ID.format(detection_id)
        response, _ = self._request(endpoint, request_type='GET')
        return response

    def get_detection_by_name(self, detection_name):
        """Get a detection by name."""
        endpoint = self.EP_DETECTION_BY_NAME.format(detection_name)
        response, _ = self._request(endpoint, request_type='GET')
        return response

    def create_detection(self, detection, active):
        """Create a detection."""
        body = {}
        body["active"] = active

        if detection.get("detection"):
            body["detection"] = detection["detection"]

        if detection.get("name"):
            body["name"] = detection["name"]

        endpoint = self.EP_DETECTIONS
        response, _ = self._request(endpoint, request_type='POST', json=body)
        return response

    # be careful what values are set in the request - they'll force an update
    def update_detection(self, detection_id, detection, active):
        """Update an org detection by ID."""
        body = {}

        if active is not None:
            body["active"] = active

        if detection.get("detection"):
            body["detection"] = detection["detection"]

        if detection.get("name"):
            body["name"] = detection["name"]

        endpoint = self.EP_DETECTION_BY_ID.format(detection_id)
        response, headers = self._request(endpoint, request_type='PATCH', json=body)

        # yeah, this is not great, but it's the best we got right now
        response["changed"] = bool(int(headers.get("sublime-entity-updated")))

        return response

    # be careful what values are set in the request - they'll force an update
    def update_detection_by_name(self, name, detection, active):
        """Update an org detection by name."""
        body = {}

        if active is not None:
            body["active"] = active

        if detection:
            body["detection"] = detection

        endpoint = self.EP_DETECTION_BY_NAME.format(name)
        response, headers = self._request(endpoint, request_type='PATCH', json=body)

        # yeah, this is not great, but it's the best we got right now
        response["changed"] = bool(int(headers.get("sublime-entity-updated")))

        return response

    def share_detection(self, detection_id, share_sublime_user=False, share_org=False):
        """Share a detection by ID."""
        body = {}
        body["share_sublime_user"] = share_sublime_user
        body["share_org"] = share_org

        endpoint = self.EP_SHARE_DETECTION_BY_ID.format(detection_id)
        response, _ = self._request(endpoint, request_type='POST', json=body)
        return response

    def unshare_detection(self, detection_id):
        """Unshare a detection by ID."""

        endpoint = self.EP_UNSHARE_DETECTION_BY_ID.format(detection_id)
        response, _ = self._request(endpoint, request_type='POST')
        return response

    def subscribe_detection(self, detection_id, active=False):
        """Subscribe to a community detection."""
        body = {}
        body["active"] = active

        endpoint = self.EP_SUBSCRIBE_DETECTION_BY_ID.format(detection_id)
        response, _ = self._request(endpoint, request_type='POST', json=body)
        return response

    def unsubscribe_detection(self, detection_id):
        """Unsubscribe from a community detection."""

        endpoint = self.EP_UNSUBSCRIBE_DETECTION_BY_ID.format(detection_id)
        response, _ = self._request(endpoint, request_type='POST')
        return response

    def get_me(self):
        """Get information about the currently authenticated Sublime user."""

        endpoint = self.EP_GET_ME
        response, _ = self._request(endpoint, request_type='GET')
        return response

    def get_org(self):
        """Get information about the currently authenticated organization."""

        endpoint = self.EP_GET_ORG
        response, _ = self._request(endpoint, request_type='GET')
        return response

    def get_org_detections(self, active=None, search=None, created_by_org_id=None,
            created_by_sublime_user_id=None):
        """Get org detections."""
        params = {}

        if active is not None:
            params["active"] = active

        if search:
            params["search"] = search

        if created_by_org_id:
            params["created_by_org_id"] = created_by_org_id

        if created_by_sublime_user_id:
            params["created_by_sublime_user_id"] = created_by_sublime_user_id

        endpoint = self.EP_ORG_DETECTIONS
        response, _ = self._request(endpoint, request_type='GET', params=params)
        return response

    def get_community_detections(self, search=None, created_by_org_id=None,
            created_by_sublime_user_id=None):
        """Get community detections."""
        params = {}

        if search:
            params["search"] = search

        if created_by_org_id:
            params["created_by_org_id"] = created_by_org_id

        if created_by_sublime_user_id:
            params["created_by_sublime_user_id"] = created_by_sublime_user_id

        endpoint = self.EP_COMMUNITY_DETECTIONS
        response, _ = self._request(endpoint, request_type='GET', params=params)
        return response

    def get_messages(self, result=True, after=None, before=None, 
            reviewed=None, safe=None, limit=None):
        """Get messages."""
        params = {}
        params["result"] = result
        params["start_time"] = after
        params["end_time"] = before
        params["inclusive"] = False
        params["limit"] = limit

        if reviewed is not None:
            params["reviewed"] = reviewed

        if safe is not None:
            params["safe"] = safe

        endpoint = self.EP_FLAGGED_MESSAGES
        response, _ = self._request(endpoint, request_type='GET', params=params)
        return response

    def get_message_details(self, message_data_model_id):
        """Get detail view of a message."""

        endpoint = self.EP_FLAGGED_MESSAGES_DETAIL.format(
                message_data_model_id)
        response, _ = self._request(endpoint, request_type='GET')
        return response

    def review_message(self, message_data_model_id, reviewed, safe):
        """Update review status of a message."""
        body = {}
        body["reviewed"] = reviewed
        body["safe"] = safe

        endpoint = self.EP_ADMIN_ACTION_REVIEW.format(message_data_model_id)
        response, _ = self._request(endpoint, request_type='POST', json=body)
        return response

    def review_all_messages(self, after, before, reviewed, safe):
        """Update review status of all messages that meet the criteria."""
        body = {}
        body["start_time"] = after
        body["end_time"] = before
        body["inclusive"] = False
        body["reviewed"] = reviewed
        body["safe"] = safe

        # we need to serialize the datetime objects in the body
        # we do this here to avoid having to change the _request method
        body = json.dumps(body, cls=JSONEncoder)
        body = json.loads(body)

        endpoint = self.EP_ADMIN_ACTION_REVIEW_ALL
        response, _ = self._request(endpoint, request_type='POST', json=body)
        return response

    def send_mock_tutorial_one(self):
        endpoint = self.EP_SEND_MOCK_TUTORIAL_ONE
        response, _ = self._request(endpoint, request_type='POST')

        return response

    def backtest_detections(self, detections, after, before, limit):
        body = {}
        body["start_time"] = after
        body["end_time"] = before
        body["inclusive"] = False
        body["detections"] = detections

        if limit:
            body["limit"] = limit

        body = json.dumps(body, cls=JSONEncoder)
        body = json.loads(body)

        endpoint = self.EP_BACKTEST_DETECTIONS
        response, _ = self._request(endpoint, request_type='POST', json=body)
        return response

    def get_users(self, license_active):
        params = {}
        params["license_active"] = license_active

        endpoint = self.EP_GET_USERS
        response, _ = self._request(endpoint, request_type='GET', params=params)

        return response

    def activate_user(self, email_address):
        endpoint = self.EP_ACTIVATE_USER.format(email_address)
        response, _ = self._request(endpoint, request_type='POST')

        return response

    def deactivate_user(self, email_address):
        endpoint = self.EP_DEACTIVATE_USER.format(email_address)
        response, _ = self._request(endpoint, request_type='POST')

        return response

    def get_job_status(self, job_id):
        endpoint = self.EP_GET_JOB_STATUS.format(job_id)
        response, _ = self._request(endpoint, request_type='GET')

        return response

    def get_job_output(self, job_id):
        endpoint = self.EP_GET_JOB_OUTPUT.format(job_id)
        response, _ = self._request(endpoint, request_type='GET')

        return response

    def delete_model_external_message(self, message_data_model_id, permanent):
        params = {}
        if permanent:
            params["permanent"] = permanent

        endpoint = self.EP_ADMIN_ACTION_DELETE.format(message_data_model_id)
        response, _ = self._request(endpoint, request_type='POST', params=params)

        return response

    def not_implemented(self, subcommand_name):
        """Send request for a not implemented CLI subcommand.

        :param subcommand_name: Name of the CLI subcommand
        :type subcommand_name: str

        """
        endpoint = self.EP_NOT_IMPLEMENTED.format(subcommand=subcommand_name)
        response, _ = self._request(endpoint)
        return response


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)
