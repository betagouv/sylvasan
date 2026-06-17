from django.contrib.auth import views as auth_views
from django.urls import path

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from users.views import CsrfView, LoggedUserView, LoginView, LogoutView, TestAuthView, UserRegistrationView

urlpatterns = [
    path("api/auth/test/", TestAuthView.as_view()),
    path("api/auth/csrf/", CsrfView.as_view()),
    path("api/auth/me/", LoggedUserView.as_view(), name="me"),
    path("api/auth/login/", LoginView.as_view()),
    path("api/auth/logout/", LogoutView.as_view()),
    path("api/auth/register/", UserRegistrationView.as_view(), name="register"),
    path("api/mobile/token/", TokenObtainPairView.as_view()),
    path("api/mobile/token/refresh/", TokenRefreshView.as_view()),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # Urls concernant la gestion du mot de passe (comptes SylvaSan)
    path(
        "modification-mot-de-passe",
        auth_views.PasswordChangeView.as_view(
            template_name="auth/password_change_form.html",
        ),
        name="password_change",
    ),
    path(
        "mot-de-passe-modifie",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="auth/password_change_done.html",
        ),
        name="password_change_done",
    ),
    path(
        "reinitialisation-mot-de-passe",
        auth_views.PasswordResetView.as_view(
            template_name="auth/password_reset_form.html",
            email_template_name="auth/password_reset_email.txt",
            subject_template_name="auth/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "email-reinitialisation-envoye",
        auth_views.PasswordResetDoneView.as_view(
            template_name="auth/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "nouveau-mot-de-passe/<uidb64>/<token>",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="auth/password_reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),
    path(
        "mot-de-passe-reinitialise",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="auth/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]
