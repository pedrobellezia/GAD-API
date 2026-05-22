from enum import Enum


class CustomErrorType(int, Enum):
    bad_request = 400
    unauthorized = 401
    forbidden = 403
    not_found = 404
    internal_server_error = 500
    payload_too_large = 413
    unsupported_media_type = 415


class CustomAppError(Exception):
    def __init__(self, message: str, error_type: CustomErrorType, **kwargs):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.extra = kwargs
