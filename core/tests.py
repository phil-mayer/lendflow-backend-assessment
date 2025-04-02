import pytest


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
        assert response.json() == { "detail": "Authentication credentials were not provided." }

    def test_endpoint_returns_error_for_disallowed_verbs(self, client, django_user_model):
        """
        Endpoint returns HTTP 405 Method Not Allowed for disallowed HTTP verbs. The endpoint only allows GET requests.
        """
        user = django_user_model.objects.create_user(username="user+1@test.com", password="test123")
        client.force_login(user)

        response_post = client.post("/api/v1/nyt-best-sellers/", data={})
        assert response_post.status_code == 405
        assert response_post.json() == { "detail": 'Method "POST" not allowed.' }

        response_patch = client.patch("/api/v1/nyt-best-sellers/", data={})
        assert response_patch.status_code == 405
        assert response_patch.json() == { "detail": 'Method "PATCH" not allowed.' }

        response_put = client.put("/api/v1/nyt-best-sellers/", data={})
        assert response_put.status_code == 405
        assert response_put.json() == { "detail": 'Method "PUT" not allowed.' }

        response_delete = client.delete("/api/v1/nyt-best-sellers/")
        assert response_delete.status_code == 405
        assert response_delete.json() == { "detail": 'Method "DELETE" not allowed.' }
