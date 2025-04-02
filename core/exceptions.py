from rest_framework import status
from rest_framework.exceptions import APIException


class ServerError(APIException):
    """
    Custom exception to handle server errors. This likely isn't provided by Django REST Framework in case developers
    want to customize/standardize the response shape.
    """

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Internal server error"
