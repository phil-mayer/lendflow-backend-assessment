from django.urls import path

from . import views

urlpatterns = [
    path("collections/nyt/books/best-sellers", views.BestSellersView.as_view(), name="index"),
]
