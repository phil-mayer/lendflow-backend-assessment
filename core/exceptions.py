from rest_framework import status
from rest_framework.exceptions import APIException


class ServerException(APIException):
    """
    Custom exception to handle server errors. This likely isn't provided by Django REST Framework in case developers
    want to customize/standardize the response shape.
    """

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Internal server error"


class BadGatewayException(APIException):
    """
    Custom exception to represent "Bad Gateway" errors (HTTP 502).
    """

    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "Gateway timeout error"


class GatewayTimeoutException(APIException):
    """
    Custom exception to represent "Gateway Timeout" errors (HTTP 504).
    """

    status_code = status.HTTP_504_GATEWAY_TIMEOUT
    default_detail = "Gateway timeout error"
