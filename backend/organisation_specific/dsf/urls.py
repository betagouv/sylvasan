from django.urls import path

from organisation_specific.dsf.views.oauth import (
    DsfOAuthAppCallbackView,
    DsfOAuthWebCallbackView,
    DsfOAuthWebLoginView,
)

urlpatterns = [
    path("dsf/oauth/app/callback/", DsfOAuthAppCallbackView.as_view(), name="dsf-oauth-app-callback"),
    path("dsf/oauth/web/callback/", DsfOAuthWebCallbackView.as_view(), name="dsf-oauth-web-callback"),
    path("dsf/oauth/web/login/", DsfOAuthWebLoginView.as_view(), name="dsf-oauth-web-login"),
]
