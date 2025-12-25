# users/urls.py

from django.urls import path
from .views import (
    LoginTemplateView,
    VerifyCodeTemplateView,
    ProfileTemplateView,
    PhoneAuthView,
    PhoneVerifyView,
    ProfileView,
    ActivateInviteView,
)

app_name = "users"

urlpatterns: list = [
    # -------------------------
    # HTML Template Views
    # -------------------------
    path("login/", LoginTemplateView.as_view(), name="login"),
    path("verify/", VerifyCodeTemplateView.as_view(), name="verify"),
    path("profile/", ProfileTemplateView.as_view(), name="profile"),

    # -------------------------
    # API Views
    # -------------------------
    path("api/phone-auth/", PhoneAuthView.as_view(), name="api_phone_auth"),
    path("api/phone-verify/", PhoneVerifyView.as_view(), name="api_phone_verify"),
    path("api/profile/", ProfileView.as_view(), name="api_profile"),
    path("api/invite/", ActivateInviteView.as_view(), name="api_invite"),
]
