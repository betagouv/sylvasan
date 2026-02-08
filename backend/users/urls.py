from django.urls import path

from users.views import LoginView, LogoutView

urlpatterns = [
    path("api/login/", LoginView.as_view()),
    path("api/logout/", LogoutView.as_view()),
]
