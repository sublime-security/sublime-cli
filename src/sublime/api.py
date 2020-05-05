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
    EP_COMMUNITY_DETECTIONS = "community/detections"
    EP_COMMUNITY_DETECTION_BY_ID = "community/detections/{}"
    EP_COMMUNITY_DETECTION_BY_NAME = "community/detections/name/{}"
    EP_SUBSCRIBE_DETECTION_BY_ID = "community/detections/{}/subscribe"
    EP_SUBSCRIBE_DETECTION_BY_NAME = "community/detections/name/{}/subscribe"
    EP_UNSUBSCRIBE_DETECTION_BY_ID = "community/detections/{}/unsubscribe"
    EP_UNSUBSCRIBE_DETECTION_BY_NAME = "community/detections/name/{}/unsubscribe"
    EP_ORG_DETECTIONS = "org/detections"
    EP_ORG_DETECTION_BY_ID = "org/detections/{}"
    EP_ORG_DETECTION_BY_NAME = "org/detections/name/{}"
    EP_SHARE_ORG_DETECTION_BY_ID = "org/detections/{}/share"
    EP_SHARE_ORG_DETECTION_BY_NAME = "org/detections/name/{}/share"
    EP_UNSHARE_ORG_DETECTION_BY_ID = "org/detections/{}/unshare"
    EP_UNSHARE_ORG_DETECTION_BY_NAME = "org/detections/name/{}/unshare"
    EP_ADMIN_ACTION_REVIEW = "actions/admin/review/{}"
    EP_ADMIN_ACTION_REVIEW_ALL = "actions/admin/review/multi/all"
    EP_ADMIN_ACTION_DELETE = "actions/admin/delete/{}"
    EP_GET_ME = "org/sublime-users/me"
    EP_GET_ORG = "org"
    EP_GET_USERS = "org/users"
    EP_FLAGGED_MESSAGES = "org/flagged-messages"
    EP_FLAGGED_MESSAGES_DETAIL = "org/flagged-messages/{}/detail"
    EP_SEND_MOCK_TUTORIAL_ONE = "org/sublime-users/mock-tutorial-one"
    EP_UPDATE_USER_LICENSE = "org/users/email/{}/license"
    EP_BACKTEST_DETECTIONS = "org/detections/backtest/multi"
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

        return body

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

    def query_mdm_multi(self, message_data_model, queries, verbose):
        """Query an enriched Message Data Model against a list of detections"""

        body = {}
        body["message_data_model"] = message_data_model
        body["queries"] = queries 
        if verbose:
            body["response_type"] = "full"
        endpoint = self.EP_MODEL_QUERY_MULTI
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
        response = self._request(endpoint, request_type='POST', json=body)
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
        response = self._request(endpoint, request_type='POST', json=body)
        return response

    def analyze_eml(self, eml, detection, mailbox_email_address, route_type, verbose):
        """Analyze an EML against a detection."""

        LOGGER.debug("Analyzing EML...")

        body = {}
        body["message"] = eml
        body["detection"] = detection
        body["mailbox_email_address"] = mailbox_email_address
        body["route_type"] = route_type

        endpoint = self.EP_MESSAGE_ANALYZE
        response = self._request(endpoint, request_type='POST', json=body)
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
        response = self._request(endpoint, request_type='POST', json=body)
        return response

    def create_org_detection(self, detection, active, verbose):
        """Create a detection."""
        body = {}
        body["active"] = active

        if detection.get("detection"):
            body["detection"] = detection["detection"]

        if detection.get("name"):
            body["name"] = detection["name"]

        if verbose:
            body["response_type"] = "full"

        endpoint = self.EP_ORG_DETECTIONS
        response = self._request(endpoint, request_type='POST', json=body)
        return response

    # be careful what values are set in the request - they'll force an update
    def update_org_detection(self, detection_id, detection, active, verbose):
        """Update an detection by ID."""
        body = {}

        if active is not None:
            body["active"] = active

        if detection.get("detection"):
            body["detection"] = detection["detection"]

        if detection.get("name"):
            body["name"] = detection["name"]

        endpoint = self.EP_ORG_DETECTION_BY_ID.format(detection_id)
        response = self._request(endpoint, request_type='PATCH', json=body)
        return response

    # be careful what values are set in the request - they'll force an update
    def update_org_detection_by_name(self, name, detection, active, verbose):
        """Update an org detection by name."""
        body = {}

        if active is not None:
            body["active"] = active

        if detection:
            body["detection"] = detection

        endpoint = self.EP_ORG_DETECTION_BY_NAME.format(name)
        response = self._request(endpoint, request_type='PATCH', json=body)
        return response

    def share_org_detection(self, detection_id, share_sublime_user=False, share_org=False):
        """Share a detection by ID."""
        body = {}
        body["share_sublime_user"] = share_sublime_user
        body["share_org"] = share_org

        endpoint = self.EP_SHARE_ORG_DETECTION_BY_ID.format(detection_id)
        response = self._request(endpoint, request_type='POST', json=body)
        return response

    def share_org_detection_by_name(self, detection_name, share_sublime_user=False, 
            share_org=False):
        """Share a detection by name."""
        body = {}
        body["share_sublime_user"] = share_sublime_user
        body["share_org"] = share_org

        endpoint = self.EP_SHARE_ORG_DETECTION_BY_NAME.format(detection_name)
        response = self._request(endpoint, request_type='POST', json=body)
        return response

    def unshare_org_detection(self, detection_id):
        """Unshare a detection by ID."""

        endpoint = self.EP_UNSHARE_ORG_DETECTION_BY_ID.format(detection_id)
        response = self._request(endpoint, request_type='POST')
        return response

    def unshare_org_detection_by_name(self, detection_name):
        """Unshare a detection by name."""

        endpoint = self.EP_UNSHARE_ORG_DETECTION_BY_NAME.format(detection_name)
        response = self._request(endpoint, request_type='POST')
        return response

    def subscribe_community_detection(self, detection_id, active=False):
        """Subscribe to a community detection."""
        body = {}
        body["active"] = active

        endpoint = self.EP_SUBSCRIBE_DETECTION_BY_ID.format(detection_id)
        response = self._request(endpoint, request_type='POST', json=body)
        return response

    def subscribe_community_detection_by_name(self, detection_name, active=False):
        """Subscribe to a community detection by name."""
        body = {}
        body["active"] = active

        endpoint = self.EP_SUBSCRIBE_DETECTION_BY_NAME.format(detection_name)
        response = self._request(endpoint, request_type='POST', json=body)
        return response

    def unsubscribe_community_detection(self, detection_id):
        """Unsubscribe from a community detection."""

        endpoint = self.EP_UNSUBSCRIBE_DETECTION_BY_ID.format(detection_id)
        response = self._request(endpoint, request_type='POST')
        return response

    def unsubscribe_community_detection_by_name(self, detection_name):
        """Unsubscribe from a community detection by name."""

        endpoint = self.EP_UNSUBSCRIBE_DETECTION_BY_NAME.format(detection_name)
        response = self._request(endpoint, request_type='POST')
        return response

    def get_me(self, verbose):
        """Get information about the currently authenticated Sublime user."""

        endpoint = self.EP_GET_ME
        response = self._request(endpoint, request_type='GET')
        return response

    def get_org(self, verbose):
        """Get information about the currently authenticated organization."""

        endpoint = self.EP_GET_ORG
        response = self._request(endpoint, request_type='GET')
        return response

    def get_org_detections(self, active=None, search=None, created_by_org_id=None,
            created_by_sublime_user_id=None):
        """Get org detections."""
        params = {}

        if active:
            params["active"] = active

        if search:
            params["search"] = search

        if created_by_org_id:
            params["created_by_org_id"] = created_by_org_id

        if created_by_sublime_user_id:
            params["created_by_sublime_user_id"] = created_by_sublime_user_id

        endpoint = self.EP_ORG_DETECTIONS
        response = self._request(endpoint, request_type='GET', params=params)
        return response

    def get_org_detection(self, detection_id, verbose):
        """Get an org detection by ID."""
        endpoint = self.EP_ORG_DETECTION_BY_ID.format(detection_id)
        response = self._request(endpoint, request_type='GET')
        return response

    def get_org_detection_by_name(self, detection_name, verbose):
        """Get an org detection by name."""
        endpoint = self.EP_ORG_DETECTION_BY_NAME.format(detection_name)
        response = self._request(endpoint, request_type='GET')
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
        response = self._request(endpoint, request_type='GET', params=params)
        return response

    def get_community_detection(self, detection_id, verbose):
        """Get a community detection by ID."""
        endpoint = self.EP_COMMUNITY_DETECTION_BY_ID.format(detection_id)
        response = self._request(endpoint, request_type='GET')
        return response

    def get_community_detection_by_name(self, detection_name, verbose):
        """Get a community detection by name."""
        endpoint = self.EP_COMMUNITY_DETECTION_BY_NAME.format(detection_name)
        response = self._request(endpoint, request_type='GET')
        return response

    def get_flagged_messages(self, result=True, after=None, before=None, 
            reviewed=False, safe=None):
        """Get flagged messages."""
        params = {}
        params["result"] = result
        params["start_time"] = after
        params["end_time"] = before
        params["inclusive"] = False
        params["reviewed"] = reviewed

        if safe is not None:
            params["safe"] = safe

        endpoint = self.EP_FLAGGED_MESSAGES
        response = self._request(endpoint, request_type='GET', params=params)
        return response

    def get_flagged_message_detail(self, message_data_model_id):
        """Get detail view of a message."""

        endpoint = self.EP_FLAGGED_MESSAGES_DETAIL.format(
                message_data_model_id)
        response = self._request(endpoint, request_type='GET')
        return response

    def review_message(self, message_data_model_id, reviewed, safe, verbose):
        """Update review status of a message."""
        body = {}
        body["reviewed"] = reviewed
        body["safe"] = safe

        endpoint = self.EP_ADMIN_ACTION_REVIEW.format(message_data_model_id)
        response = self._request(endpoint, request_type='POST', json=body)
        return response

    def review_all_messages(self, after, before, reviewed, safe, verbose):
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
        response = self._request(endpoint, request_type='POST', json=body)
        return response

    def send_mock_tutorial_one(self, verbose):
        endpoint = self.EP_SEND_MOCK_TUTORIAL_ONE
        response = self._request(endpoint, request_type='POST')

        return response

    def backtest_detections(self, detections, after, before):
        body = {}
        body["start_time"] = after
        body["end_time"] = before
        body["inclusive"] = False
        body["detections"] = detections

        body = json.dumps(body, cls=JSONEncoder)
        body = json.loads(body)

        endpoint = self.EP_BACKTEST_DETECTIONS
        response = self._request(endpoint, request_type='POST', json=body)
        return response

    def update_user_license(self, email_address, license_active, verbose):
        body = {}
        body["license_active"] = license_active

        endpoint = self.EP_UPDATE_USER_LICENSE.format(email_address)
        response = self._request(endpoint, request_type='PATCH', json=body)

        return response

    def get_users(self, license_active, verbose):
        params = {}
        params["license_active"] = license_active

        endpoint = self.EP_GET_USERS
        response = self._request(endpoint, request_type='GET', params=params)

        return response

    def get_job_status(self, job_id):
        endpoint = self.EP_GET_JOB_STATUS.format(job_id)
        response = self._request(endpoint, request_type='GET')

        return response

    def get_job_output(self, job_id):
        endpoint = self.EP_GET_JOB_OUTPUT.format(job_id)
        response = self._request(endpoint, request_type='GET')

        return response

    def delete_model_external_message(self, message_data_model_id, permanent):
        params = {}
        if permanent:
            params["permanent"] = permanent

        endpoint = self.EP_ADMIN_ACTION_DELETE.format(message_data_model_id)
        response = self._request(endpoint, request_type='DELETE', params=params)

        return response

    def not_implemented(self, subcommand_name):
        """Send request for a not implemented CLI subcommand.

        :param subcommand_name: Name of the CLI subcommand
        :type subcommand_name: str

        """
        endpoint = self.EP_NOT_IMPLEMENTED.format(subcommand=subcommand_name)
        response = self._request(endpoint)
        return response


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)
