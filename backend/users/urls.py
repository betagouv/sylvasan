from django.urls import path

from users.views import CsrfView, LoginView, LogoutView

urlpatterns = [
    path("api/csrf/", CsrfView.as_view()),
    path("api/login/", LoginView.as_view()),
    path("api/logout/", LogoutView.as_view()),
]
