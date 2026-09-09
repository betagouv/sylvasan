from django.urls import path

from stats.views import StatsAPIView

urlpatterns = [
    path("api/stats/", StatsAPIView.as_view(), name="stats"),
]
