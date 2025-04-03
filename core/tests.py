from unittest.mock import Mock, patch

import pytest
from django.core.cache import cache
from django.utils.http import urlencode
from requests.exceptions import Timeout as TimeoutException


@pytest.fixture(autouse=True)
def reset_cache():
    """Clear the application cache before each test run."""
    cache.clear()


@pytest.fixture
def book_with_long_title():
    return {
        "author": "Test Author",
        "title": "The Life and Times of a Test Author: A Test Data Story Told as an Epic Poem with Supplementary Commentary by Several Other Test Authors (Abridged)",  # noqa: E501
        "isbns": [{"isbn10": "fake", "isbn13": "fake"}],
    }


@pytest.fixture
def book_beren_and_luthien():
    """Data provided by The New York Times."""
    return {
        "author": "JRR Tolkien",
        "title": "BEREN AND LÚTHIEN",
        "isbns": [{"isbn10": "1328791823", "isbn13": "9781328791825"}],
    }


@pytest.fixture
def book_the_fall_of_goldolin():
    """Data provided by The New York Times."""
    return {
        "author": "JRR Tolkien",
        "title": "THE FALL OF GONDOLIN",
        "isbns": [
            {"isbn10": "1328613046", "isbn13": "9781328613042"},
            {"isbn10": "1328612996", "isbn13": "9781328612991"},
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

    def test_endpoint_validates_the_author_query_param(
        self, client, django_user_model, book_beren_and_luthien, book_the_fall_of_goldolin
    ):
        """
        Endpoint returns HTTP 400 if the `author` query parameter is passed with a length greater than 32 characters.
        """
        user = django_user_model.objects.create_user(username="user+1@test.com", password="test123")
        client.force_login(user)

        response_long_param = client.get(
            f"/api/v1/nyt-best-sellers/?{urlencode({'author': 'THIS_STRING_IS_33_CHARACTERS_BBBB'})}"
        )
        assert response_long_param.status_code == 400
        assert response_long_param.json() == {"author": ["Ensure this field has no more than 32 characters."]}

        with patch(
            "requests.get",
            Mock(
                side_effect=[
                    Mock(
                        status_code=200,
                        json=lambda: {"num_results": 2, "results": [book_beren_and_luthien, book_the_fall_of_goldolin]},
                    ),
                    Mock(status_code=200, json=lambda: {"num_results": 0, "results": []}),
                ]
            ),
        ) as mock_integration_http_call:
            assert mock_integration_http_call.call_count == 0

            response_valid_param = client.get(f"/api/v1/nyt-best-sellers/?{urlencode({'author': 'JRR Tolkien'})}")

            assert mock_integration_http_call.call_count == 1
            assert response_valid_param.status_code == 200
            assert response_valid_param.json() == {
                "num_results": 2,
                "results": [book_beren_and_luthien, book_the_fall_of_goldolin],
            }

            response_valid_param_boundary = client.get(
                f"/api/v1/nyt-best-sellers/?{urlencode({'author': 'A_32_CHARACTER_LONG_STRING_AAAAA'})}"
            )

            assert mock_integration_http_call.call_count == 2
            assert response_valid_param_boundary.status_code == 200
            assert response_valid_param_boundary.json() == {"num_results": 0, "results": []}

    def test_endpoint_validates_the_title_query_param(self, client, django_user_model, book_with_long_title):
        """
        Endpoint returns HTTP 400 if the `title` query parameter is passed with a length greater than 128 characters.
        """
        user = django_user_model.objects.create_user(username="user+1@test.com", password="test123")
        client.force_login(user)

        response_long_param = client.get(
            f"/api/v1/nyt-best-sellers/?{urlencode({'title': 'Another Extremely Long Title That Exceeds the 128 Character Limit for this Test Case: The Epic Story of How I Wrote a Very Long String'})}"  # noqa: E501
        )
        assert response_long_param.status_code == 400
        assert response_long_param.json() == {"title": ["Ensure this field has no more than 128 characters."]}

        with patch(
            "requests.get",
            Mock(
                return_value=Mock(status_code=200, json=lambda: {"num_results": 1, "results": [book_with_long_title]})
            ),
        ) as mock_integration_http_call:
            assert mock_integration_http_call.call_count == 0

            response_valid_param = client.get(
                f"/api/v1/nyt-best-sellers/?{urlencode({'title': 'The Life and Times of a Test Author'})}"
            )

            assert mock_integration_http_call.call_count == 1
            assert response_valid_param.status_code == 200
            assert response_valid_param.json() == {"num_results": 1, "results": [book_with_long_title]}

            response_valid_param_boundary = client.get(
                f"/api/v1/nyt-best-sellers/?{urlencode({'title': 'The Life and Times of a Test Author: A Test Data Story Told as an Epic Poem with Supplementary Commentary by Several Other Test '})}"  # noqa: E501
            )

            assert mock_integration_http_call.call_count == 2
            assert response_valid_param_boundary.status_code == 200
            assert response_valid_param_boundary.json() == {"num_results": 1, "results": [book_with_long_title]}

    def test_endpoint_validates_the_offset_query_param(self, client, django_user_model, book_the_fall_of_goldolin):
        """
        Endpoint returns HTTP 400 if the `offset` query parameter is passed with a negative value, or a value that is
        not a multiple of 20 (the source API's fixed page size).
        """
        user = django_user_model.objects.create_user(username="user+1@test.com", password="test123")
        client.force_login(user)

        response_both_errors = client.get(f"/api/v1/nyt-best-sellers/?{urlencode({'offset': -1})}")
        assert response_both_errors.status_code == 400
        assert response_both_errors.json() == {
            "offset": ["Ensure this value is a multiple of 20.", "Ensure this value is greater than or equal to 0."]
        }

        response_negative = client.get(f"/api/v1/nyt-best-sellers/?{urlencode({'offset': -20})}")
        assert response_negative.status_code == 400
        assert response_negative.json() == {"offset": ["Ensure this value is greater than or equal to 0."]}

        response_not_multiple_of_20 = client.get(f"/api/v1/nyt-best-sellers/?{urlencode({'offset': 5})}")
        assert response_not_multiple_of_20.status_code == 400
        assert response_not_multiple_of_20.json() == {"offset": ["Ensure this value is a multiple of 20."]}

        with patch(
            "requests.get",
            Mock(
                side_effect=[
                    Mock(status_code=200, json=lambda: {"num_results": 1, "results": [book_the_fall_of_goldolin]}),
                    Mock(status_code=200, json=lambda: {"num_results": 0, "results": []}),
                ]
            ),
        ) as mock_integration_http_call:
            assert mock_integration_http_call.call_count == 0

            response_zero_offset = client.get(
                f"/api/v1/nyt-best-sellers/?{urlencode({'offset': 0, 'title': 'THE FALL OF GONDOLIN'})}"
            )

            assert mock_integration_http_call.call_count == 1
            assert response_zero_offset.status_code == 200
            assert response_zero_offset.json() == {"num_results": 1, "results": [book_the_fall_of_goldolin]}

            response_offset_above_result_limit = client.get(
                f"/api/v1/nyt-best-sellers/?{urlencode({'offset': 20, 'title': 'THE FALL OF GONDOLIN'})}"
            )

            assert mock_integration_http_call.call_count == 2
            assert response_offset_above_result_limit.status_code == 200
            assert response_offset_above_result_limit.json() == {"num_results": 0, "results": []}

    def test_endpoint_validates_the_isbn_array_query_param(self, client, django_user_model, book_beren_and_luthien):
        """
        Endpoint returns HTTP 400 if the `isbn[]` query parameter is passed values of incorrect length (10 or 13
        characters), contains non-numeric characters, or more than 2 values.
        """
        user = django_user_model.objects.create_user(username="user+1@test.com", password="test123")
        client.force_login(user)
        # This example violates all validation, but since we use custom Django REST Framework `validators` for this
        # parameter, the first custom error will be reported.
        # Also, we can't URL-encode the query parameters in a single call because `urlencode` returns a `dict`.
        response_all_errors = client.get(
            f"/api/v1/nyt-best-sellers/?{urlencode({'isbn[]': 1})}&{urlencode({'isbn[]': 'ABCDEFGHIJ'})}&{urlencode({'isbn[]': '1328791823'})}"  # noqa: E501
        )
        assert response_all_errors.status_code == 400
        assert response_all_errors.json() == {"isbn": ["Ensure up to 2 ISBNs are provided."]}

        response_too_many_values = client.get(
            f"/api/v1/nyt-best-sellers/?{urlencode({'isbn[]': '1328791823'})}&{urlencode({'isbn[]': '1328613046'})}&{urlencode({'isbn[]': '1328612996'})}"  # noqa: E501
        )
        assert response_too_many_values.status_code == 400
        assert response_too_many_values.json() == {"isbn": ["Ensure up to 2 ISBNs are provided."]}

        response_non_numeric_value = client.get(f"/api/v1/nyt-best-sellers/?{urlencode({'isbn[]': 'ABCDEFGHIJ'})}")
        assert response_non_numeric_value.status_code == 400
        assert response_non_numeric_value.json() == {"isbn": ["Ensure each ISBN only contains digits."]}

        response_incorrect_length = client.get(f"/api/v1/nyt-best-sellers/?{urlencode({'isbn[]': '1'})}")
        assert response_incorrect_length.status_code == 400
        assert response_incorrect_length.json() == {"isbn": ["Ensure each ISBN is either 10 or 13 characters long."]}

        with patch(
            "requests.get",
            Mock(
                side_effect=[
                    Mock(status_code=200, json=lambda: {"num_results": 1, "results": [book_beren_and_luthien]}),
                    Mock(status_code=200, json=lambda: {"num_results": 0, "results": []}),
                ]
            ),
        ) as mock_integration_http_call:
            assert mock_integration_http_call.call_count == 0

            response_one_param = client.get(f"/api/v1/nyt-best-sellers/?{urlencode({'isbn[]': '1328791823'})}")
            assert mock_integration_http_call.call_count == 1
            assert response_one_param.status_code == 200
            assert response_one_param.json() == {"num_results": 1, "results": [book_beren_and_luthien]}

            # Using the two real books in the fixtures above, it doesn't seem that the source NYT API is doing an OR
            # operation when multiple ISBNs are provided. It might be a bug. For now, this test mimics the behavior I've
            # observed in production.
            response_two_params = client.get(
                f"/api/v1/nyt-best-sellers/?{urlencode({'isbn[]': '1328791823'})}&{urlencode({'isbn[]': '1328613046'})}"
            )
            assert mock_integration_http_call.call_count == 2
            assert response_two_params.status_code == 200
            assert response_two_params.json() == {"num_results": 0, "results": []}

    def test_endpoint_uses_cache_for_repeated_calls(self, client, django_user_model, book_beren_and_luthien):
        """
        Endpoint uses the cache when repeated calls are made with the same (known) query parameters.
        """
        user = django_user_model.objects.create_user(username="user+1@test.com", password="test123")
        client.force_login(user)

        with patch(
            "requests.get",
            Mock(
                return_value=Mock(status_code=200, json=lambda: {"num_results": 1, "results": [book_beren_and_luthien]})
            ),
        ) as mock_integration_http_call:
            assert mock_integration_http_call.call_count == 0

            response_cache_miss = client.get(
                f"/api/v1/nyt-best-sellers/?{urlencode({'author': 'JRR Tolkien', 'isbn[]': '1328791823', 'offset': 0, 'title': 'BEREN'})}"  # noqa: E501
            )
            assert mock_integration_http_call.call_count == 1
            assert response_cache_miss.status_code == 200
            assert response_cache_miss.json() == {"num_results": 1, "results": [book_beren_and_luthien]}

            # Same URL
            response_cache_hit_unknown_param = client.get(
                f"/api/v1/nyt-best-sellers/?{urlencode({'author': 'JRR Tolkien', 'isbn[]': '1328791823', 'offset': 0, 'title': 'BEREN'})}"  # noqa: E501
            )
            assert mock_integration_http_call.call_count == 1
            assert response_cache_hit_unknown_param.status_code == 200
            assert response_cache_hit_unknown_param.json() == {"num_results": 1, "results": [book_beren_and_luthien]}

            # Same URL, extraneous parameter
            response_cache_hit_unknown_param = client.get(
                f"/api/v1/nyt-best-sellers/?{urlencode({'unknown-param': 'unknown-value', 'author': 'JRR Tolkien', 'isbn[]': '1328791823', 'offset': 0, 'title': 'BEREN'})}"  # noqa: E501
            )
            assert mock_integration_http_call.call_count == 1
            assert response_cache_hit_unknown_param.status_code == 200
            assert response_cache_hit_unknown_param.json() == {"num_results": 1, "results": [book_beren_and_luthien]}
