import logging

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from requests.exceptions import Timeout as TimeoutException
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .exceptions import BadGatewayException, GatewayTimeoutException, ServerException
from .services import NYTApiService

logger = logging.getLogger(__name__)


# The following serializer classes are underscored to indicate that they are private to this file. In a normal Django
# application, I would consider **models** to be reusable across files/modules. These serializers should be considered
# part of the "presentation layer" for these routes (i.e. Django views).


class _BestSellersFilterSerializer(serializers.Serializer):
    """
    Serializer class for the allowed filter criteria (via query params).
    """

    author = serializers.CharField(max_length=32, required=False)


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
                description="Author name.",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
            )
        ],
        responses={
            200: _BestSellersResponseSerializer,
            400: serializers.ValidationError,
        },
    )
    def list(self, request, *args, **kwargs):
        """
        Retrieve a list of New York Times Books Best Sellers based on the provided filter criteria. This endpoint
        proxies the request to NYT's API, which uses a fixed page size of 20. For this reason, requests to this endpoint
        must use the returned `num_results` key to paginate through the results with the `offset` query parameter.

        TODO: implement the following:

        - offset query param
        - isbn[] query param
        - title query param
        """
        filter_params = {}
        if "author" in request.query_params:
            filter_params["author"] = request.query_params["author"]

        filter_criteria_serializer = _BestSellersFilterSerializer(data=filter_params)
        filter_criteria_serializer.is_valid(raise_exception=True)

        try:
            data = NYTApiService.get_best_sellers(filter_criteria=filter_criteria_serializer.validated_data)
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
                "num_results": data.get("num_results", 0),
                "results": data.get("results", []),
            }
        )
        return Response(data=response_serializer.data, status=status.HTTP_200_OK)
