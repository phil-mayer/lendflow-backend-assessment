import logging

from rest_framework import permissions, viewsets
from rest_framework.response import Response

from .exceptions import ServerError
from .services import NYTApiService

logger = logging.getLogger(__name__)


class NYTBestSellersViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = None

    def list(self, request, *args, **kwargs):
        """
        Retrieve a list of New York Times Books Best Sellers based on the provided filter criteria. This endpoint
        proxies the request to NYT's API, which uses a fixed page size of 20. For this reason, requests to this endpoint
        must use the returned `num_results` key to paginate through the results with the `offset` query parameter.

        TODO: implement the following:

        - offset query param
        - author query param
        - isbn[] query param
        - title query param
        - return HTTP 401 if the user is not authenticated (currently returning HTTP 403 by default).
        """
        try:
            data = NYTApiService.get_best_sellers()
        except Exception as e:
            logger.warning("[NYTBestSellersViewSet] Failed to retrieve NYT Best Sellers")
            raise ServerError(detail="Failed to retrieve data from source") from e

        return Response(data={"num_results": data.get("num_results"), "results": data.get("results")})
