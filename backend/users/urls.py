from django.urls import path

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from users.views import CsrfView, LoggedUserView, LoginView, LogoutView, TestAuthView

urlpatterns = [
    path("api/auth/test/", TestAuthView.as_view()),
    path("api/auth/csrf/", CsrfView.as_view()),
    path("api/auth/me/", LoggedUserView.as_view()),
    path("api/auth/login/", LoginView.as_view()),
    path("api/auth/logout/", LogoutView.as_view()),
    path("api/mobile/token/", TokenObtainPairView.as_view()),
    path("api/mobile/token/refresh/", TokenRefreshView.as_view()),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
]
