from django.contrib.auth import get_user_model, login
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View

from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from users.serializers import UserRegistrationSerializer

User = get_user_model()


def _send_verification_email(user, request):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    protocol = "https" if request.is_secure() else "http"
    domain = request.get_host()

    message = render_to_string(
        "auth/email_verification_email.txt",
        {"user": user, "uid": uid, "token": token, "protocol": protocol, "domain": domain},
    )
    send_mail(
        subject="Vérifiez votre adresse email Sylva-San",
        message=message,
        from_email=None,
        recipient_list=[user.email],
    )


class UserRegistrationView(CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        _send_verification_email(user, self.request)


class EmailVerificationView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save(update_fields=["is_active"])
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("/")

        return redirect("/s-identifier?verification_failed=1")
