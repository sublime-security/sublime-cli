"""Sublime API client exceptions."""


class RequestFailure(Exception):
    """Exception to capture a failed request."""


class RateLimitError(RequestFailure):
    """API rate limit passed."""


class WebSocketError(Exception):
    """Websocket Error"""


class JobError(Exception):
    """Exceptions on job execution"""
