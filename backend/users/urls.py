from django.urls import path

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views import CsrfView, LoggedUserView, LoginView, LogoutView

urlpatterns = [
    path("api/auth/csrf/", CsrfView.as_view()),
    path("api/auth/me/", LoggedUserView.as_view()),
    path("api/auth/login/", LoginView.as_view()),
    path("api/auth/logout/", LogoutView.as_view()),
    path("api/mobile/token/", TokenObtainPairView.as_view()),
    path("api/mobile/token/refresh/", TokenRefreshView.as_view()),
]
