from unittest.mock import Mock, patch

import pytest
from django.utils.http import urlencode
from requests.exceptions import Timeout as TimeoutException


@pytest.fixture
def tolkien_books():
    """
    Data fixture usable in tests below. Data provided by The New York Times.
    """
    return {
        "num_results": 2,
        "results": [
            {
                "author": "JRR Tolkien",
                "title": "BEREN AND LÚTHIEN",
                "isbns": [{"isbn10": "1328791823", "isbn13": "9781328791825"}],
            },
            {
                "author": "JRR Tolkien",
                "title": "THE FALL OF GONDOLIN",
                "isbns": [
                    {"isbn10": "1328613046", "isbn13": "9781328613042"},
                    {"isbn10": "1328612996", "isbn13": "9781328612991"},
                ],
            },
        ],
    }


@pytest.mark.django_db
class TestNYTBestSellersViewSetView:
    def test_endpoint_returns_error_if_not_authenticated(self, client):
        """
        Endpoint returns HTTP 403 Forbidden if the user is not authenticated. Django REST Framework returns HTTP 403
        instead of HTTP 401 when the user is not authenticated and session authentication is used because it does not
        include a `WWW-Authenticate` header in the response.

        See: https://stackoverflow.com/a/6937030/3942157
        """
        response = client.get("/api/v1/nyt-best-sellers/")
        assert response.status_code == 403
        assert response.json() == {"detail": "Authentication credentials were not provided."}

    def test_endpoint_returns_error_for_disallowed_verbs(self, client, django_user_model):
        """
        Endpoint returns HTTP 405 Method Not Allowed for disallowed HTTP verbs. The endpoint only allows GET requests.
        """
        user = django_user_model.objects.create_user(username="user+1@test.com", password="test123")
        client.force_login(user)

        response_post = client.post("/api/v1/nyt-best-sellers/", data={})
        assert response_post.status_code == 405
        assert response_post.json() == {"detail": 'Method "POST" not allowed.'}

        response_patch = client.patch("/api/v1/nyt-best-sellers/", data={})
        assert response_patch.status_code == 405
        assert response_patch.json() == {"detail": 'Method "PATCH" not allowed.'}

        response_put = client.put("/api/v1/nyt-best-sellers/", data={})
        assert response_put.status_code == 405
        assert response_put.json() == {"detail": 'Method "PUT" not allowed.'}

        response_delete = client.delete("/api/v1/nyt-best-sellers/")
        assert response_delete.status_code == 405
        assert response_delete.json() == {"detail": 'Method "DELETE" not allowed.'}

    def test_endpoint_returns_error_if_proxy_unsuccessful(self, client, django_user_model):
        """
        Endpoint returns HTTP 500 if the source API returns a response code greater than 200 and less than 500 (error
        could be our fault). Returns HTTP 502 if the source API returns a 5XX response code. Returns HTTP 504 if the
        proxy request timed out.
        """
        user = django_user_model.objects.create_user(username="user+1@test.com", password="test123")
        client.force_login(user)

        with patch(
            "requests.get",
            Mock(
                side_effect=[
                    Mock(status_code=204),
                    Mock(status_code=301),
                    Mock(status_code=400),
                    Mock(status_code=500),
                    TimeoutException(),
                ]
            ),
        ) as mock_integration_http_call:
            assert mock_integration_http_call.call_count == 0

            response_204_side_effect = client.get("/api/v1/nyt-best-sellers/")

            assert mock_integration_http_call.call_count == 1
            assert response_204_side_effect.status_code == 500
            assert response_204_side_effect.json() == {"detail": "Failed to retrieve data from source API."}

            response_301_side_effect = client.get("/api/v1/nyt-best-sellers/")

            assert mock_integration_http_call.call_count == 2
            assert response_301_side_effect.status_code == 500
            assert response_301_side_effect.json() == {"detail": "Failed to retrieve data from source API."}

            response_400_side_effect = client.get("/api/v1/nyt-best-sellers/")

            assert mock_integration_http_call.call_count == 3
            assert response_400_side_effect.status_code == 500
            assert response_400_side_effect.json() == {"detail": "Failed to retrieve data from source API."}

            response_500_side_effect = client.get("/api/v1/nyt-best-sellers/")

            assert mock_integration_http_call.call_count == 4
            assert response_500_side_effect.status_code == 502
            assert response_500_side_effect.json() == {"detail": "Source API error."}

            response_timeout_side_effect = client.get("/api/v1/nyt-best-sellers/")

            assert mock_integration_http_call.call_count == 5
            assert response_timeout_side_effect.status_code == 504
            assert response_timeout_side_effect.json() == {
                "detail": "Request timed out while retrieving data from source API."
            }

    def test_endpoint_validates_the_author_query_param(self, client, django_user_model, tolkien_books):
        """
        Endpoint returns HTTP 200 if the `author` query parameter is provided and passes validation. Returns HTTP 400 if
        the `author` query parameter is passed with a length greater than 32 characters.
        """
        user = django_user_model.objects.create_user(username="user+1@test.com", password="test123")
        client.force_login(user)

        with patch(
            "requests.get",
            Mock(side_effect=[
                Mock(status_code=200, json=lambda: tolkien_books),
                Mock(status_code=200, json=lambda: { "num_results": 0, "results": [] }),
            ]),
        ) as mock_integration_http_call:
            assert mock_integration_http_call.call_count == 0

            response_valid_query_params = client.get(
                f"/api/v1/nyt-best-sellers/?{urlencode({'author': 'JRR Tolkien'})}"
            )

            assert mock_integration_http_call.call_count == 1
            assert response_valid_query_params.status_code == 200
            # Repetitive to make sure the fixture data is actually returned.
            assert response_valid_query_params.json() == {
                "num_results": 2,
                "results": [
                    {
                        "author": "JRR Tolkien",
                        "title": "BEREN AND LÚTHIEN",
                        "isbns": [{"isbn10": "1328791823", "isbn13": "9781328791825"}],
                    },
                    {
                        "author": "JRR Tolkien",
                        "title": "THE FALL OF GONDOLIN",
                        "isbns": [
                            {"isbn10": "1328613046", "isbn13": "9781328613042"},
                            {"isbn10": "1328612996", "isbn13": "9781328612991"},
                        ],
                    },
                ],
            }

            # Boundary case.
            response_valid_query_params = client.get(
                f"/api/v1/nyt-best-sellers/?{urlencode({'author': 'A_32_CHARACTER_LONG_STRING_AAAAA'})}"
            )

            assert mock_integration_http_call.call_count == 2
            assert response_valid_query_params.status_code == 200
            # Repetitive to make sure the fixture data is actually returned.
            assert response_valid_query_params.json() == { "num_results": 0, "results": [] }

        response = client.get(
            f"/api/v1/nyt-best-sellers/?{urlencode({'author': 'THIS_STRING_IS_33_CHARACTERS_BBBB'})}"
        )
        assert mock_integration_http_call.call_count == 2
        assert response.status_code == 400
        assert response.json() == {"author": ["Ensure this field has no more than 32 characters."]}
