from django.urls import path

from core.views.nyt_best_sellers_view import NYTBestSellersViewSet

urlpatterns = [
    path(
        "nyt-best-sellers/",
        NYTBestSellersViewSet.as_view({"get": "list"}),
        name="nyt-best-sellers",
    ),
]
