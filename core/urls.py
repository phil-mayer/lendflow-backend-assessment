from django.urls import path

from . import views

urlpatterns = [
    path(
        "nyt-best-sellers/",
        views.NYTBestSellersViewSet.as_view({"get": "list"}),
        name="nyt-best-sellers",
    ),
]
