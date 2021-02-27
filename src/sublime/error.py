"""Sublime API client errors."""


class SublimeError(Exception):
    def __init__(
        self,
        message=None,
        status_code=None,
        headers=None
    ):
        super(SublimeError, self).__init__(message)

        self._message = message
        self.status_code = status_code
        self.headers = headers or {}
        self.request_id = self.headers.get("x-request-id", None)

    def __str__(self):
        msg = self._message or "<empty message>"
        if self.request_id is not None:
            return u"Request {0}: {1}".format(self.request_id, msg)
        else:
            return msg

    @property
    def message(self):
        return self._message

    def __repr__(self):
        return "%s(message=%r, http_status=%r, request_id=%r)" % (
            self.__class__.__name__,
            self._message,
            self.status_code,
            self.request_id,
        )


class InvalidRequestError(SublimeError):
    """Invalid request (HTTP 400 or 404)."""


class RateLimitError(SublimeError):
    """API rate limit exceeded."""


class APIError(SublimeError):
    """All other failed requests."""


class AuthenticationError(SublimeError):
    """Invalid or missing authentiction."""


class LoadRuleError(SublimeError):
    """Error loading rules file."""


class LoadMessageDataModelError(SublimeError):
    """Error loading Message Data Model file."""


class LoadEMLError(SublimeError):
    """Error loading .EML."""


class LoadMSGError(SublimeError):
    """Error loading .MSG."""


class LoadMBOXError(SublimeError):
    """Error loading .MBOX."""
