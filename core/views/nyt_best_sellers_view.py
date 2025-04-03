import logging

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, OpenApiTypes, extend_schema
from requests.exceptions import Timeout as TimeoutException
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.exceptions import BadGatewayException, GatewayTimeoutException, ServerException
from core.services.nyt_api_service import NYTApiService

logger = logging.getLogger(__name__)

# Note: If you're not familiar with Django and Django REST Framework, I recommend skipping down to line ~169.
# Since the endpoint is a proxy for another API rather than an interface for CRUD operations on database models, the
# framework can't automatically generate/discover usage information for the endpoint. Lines 84-167 are essentially
# configuration/documentation for SwaggerUI.


class _BestSellersFilterSerializer(serializers.Serializer):
    """
    Serializer class for the allowed filter criteria (via query params).
    """

    def _validate_isbn_entries(value):
        isbns = value.split(";")
        if len(isbns) > 2:
            raise ValidationError(detail="Ensure up to 2 ISBNs are provided.")

        for isbn in isbns:
            if len(isbn) not in (10, 13):
                raise ValidationError(detail="Ensure each ISBN is either 10 or 13 characters long.")
            if not isbn.isdigit():
                raise ValidationError(detail="Ensure each ISBN only contains digits.")

    def _validate_offset(value):
        if not value % 20 == 0:
            raise ValidationError(detail="Ensure this value is a multiple of 20.")

    author = serializers.CharField(max_length=32, required=False)
    isbn = serializers.CharField(required=False, validators=[_validate_isbn_entries])
    offset = serializers.IntegerField(min_value=0, required=False, validators=[_validate_offset])
    title = serializers.CharField(max_length=128, required=False)


class _IsbnSerializer(serializers.Serializer):
    """
    Serializer class for representating ISBN numbers for a book.
    """

    isbn10 = serializers.CharField()
    isbn13 = serializers.CharField()


class _BestSellersModelSerializer(serializers.Serializer):
    """
    Serializer class for representating a book within a successful response.
    """

    author = serializers.CharField()
    title = serializers.CharField()
    isbns = serializers.ListSerializer(child=_IsbnSerializer())


class _BestSellersResponseSerializer(serializers.Serializer):
    """
    Serializer class for successful responses.
    """

    num_results = serializers.IntegerField()
    results = serializers.ListSerializer(child=_BestSellersModelSerializer())


class NYTBestSellersViewSet(viewsets.ViewSet):
    """
    Controller (i.e. Django REST Framework view set) for the proxy New York Times Books Best Sellers API.
    """

    permission_classes = [permissions.IsAuthenticated]
    queryset = None

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="author",
                description="Author name, up to a maximum of 32 characters.",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="isbn[]",
                description="Book ISBN, either ISBN10 or ISBN13. Do not include hyphens. Provide up to two values.",
                required=False,
                many=True,
                type=str,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="offset",
                description="Result offset. The source API has a fixed page size of 20, so this must be a multiple of 20.",  # noqa: E501
                required=False,
                type=int,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="title",
                description="Book title, up to a maximum of 128 characters.",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={
            200: _BestSellersResponseSerializer,
            400: OpenApiResponse(
                description="Bad request, typically due to invalid query parameters.",
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        "HTTP 400 Example",
                        response_only=True,
                        summary="Author name too long",
                        value={"author": ["Ensure this field has no more than 32 characters."]},
                    ),
                ],
            ),
            500: OpenApiResponse(
                description="Internal server error, i.e. an unexpected error occurred in this API.",
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        "HTTP 500 Example",
                        response_only=True,
                        summary="Internal server error",
                        value={"detail": "Failed to retrieve data from source API."},
                    ),
                ],
            ),
            502: OpenApiResponse(
                description="Bad Gateway error, i.e. an unexpected error occurred in the source API.",
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        "HTTP 502 Example",
                        response_only=True,
                        summary="Bad Gateway error",
                        value={"detail": "Source API error."},
                    ),
                ],
            ),
            504: OpenApiResponse(
                description="Gateway timeout error, i.e. the request to the source API timed out.",
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        "HTTP 504 Example",
                        response_only=True,
                        summary="Gateway timeout",
                        value={"detail": "Request timed out while retrieving data from source API."},
                    ),
                ],
            ),
        },
    )
    @method_decorator(cache_page(60 * 60 * 1))
    def list(self, request):
        """
        Retrieve a list of New York Times Books Best Sellers based on the provided filter criteria. This endpoint
        proxies the request to NYT's API, which uses a fixed page size of 20. For this reason, requests to this endpoint
        must use the returned `num_results` key to paginate through the results with the `offset` query parameter.

        Note: the application caches responses for one hour. Django automatically keys the entries by URL, plus some
        request headers.

        Data provided by The New York Times.
        """
        filter_params = {}
        if "author" in request.query_params:
            filter_params["author"] = request.query_params["author"]
        if "isbn[]" in request.query_params:
            raw_isbn_list = request.query_params.copy().pop("isbn[]")
            filter_params["isbn"] = ";".join(raw_isbn_list)
        if "offset" in request.query_params:
            filter_params["offset"] = request.query_params["offset"]
        if "title" in request.query_params:
            filter_params["title"] = request.query_params["title"]

        filter_criteria_serializer = _BestSellersFilterSerializer(data=filter_params)
        filter_criteria_serializer.is_valid(raise_exception=True)

        try:
            source_api_response = NYTApiService.get_best_sellers(
                filter_criteria=filter_criteria_serializer.validated_data
            )
        except BadGatewayException as e:
            logger.warning("[NYTBestSellersViewSet] Encountered source API error while retrieving NYT Best Sellers")
            raise BadGatewayException(detail="Source API error.") from e
        except TimeoutException as e:
            logger.warning("[NYTBestSellersViewSet] Request timed out while retrieving NYT Best Sellers")
            raise GatewayTimeoutException(detail="Request timed out while retrieving data from source API.") from e
        except Exception as e:
            logger.error("[NYTBestSellersViewSet] Failed to retrieve NYT Best Sellers", exc_info=True)
            raise ServerException(detail="Failed to retrieve data from source API.") from e

        response_serializer = _BestSellersResponseSerializer(
            {
                "num_results": source_api_response.get("num_results", 0),
                "results": source_api_response.get("results", []),
            }
        )
        return Response(data=response_serializer.data, status=status.HTTP_200_OK)
