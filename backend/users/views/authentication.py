from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db.models import Q
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from users.serializers import SimpleUserSerializer


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    def get(self, request, format=None):
        return Response({"ok": True})


class LoggedUserView(APIView):
    def get(self, request, *args, **kwargs):
        """Retourne les données d'un utilisateur connecté"""

        user = request.user
        if user.is_active:
            return Response(SimpleUserSerializer(user).data)
        return Response(None, status=status.HTTP_204_NO_CONTENT)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        username_or_email = request.data.get("username")
        password = request.data.get("password")

        incomplete_data_msg = "Veuillez fournir un identifiant et un mot de passe."
        unauthorized_msg = "Ce couple identifiant/mot de passe ne permet pas de vous identifier."

        if not username_or_email or not password:
            return Response({"error": incomplete_data_msg}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = get_user_model().objects.get(Q(username=username_or_email) | Q(email=username_or_email))
        except get_user_model().DoesNotExist:
            return Response({"error": unauthorized_msg}, status=status.HTTP_401_UNAUTHORIZED)

        authenticated_user = authenticate(request, username=user.username, password=password)
        if not authenticated_user:
            return Response({"error": unauthorized_msg}, status=status.HTTP_401_UNAUTHORIZED)

        login(request, authenticated_user)
        return Response(
            {
                "csrf_token": get_token(request),
                "user": SimpleUserSerializer(user).data,
            }
        )


class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        logout(request)
        return Response()
