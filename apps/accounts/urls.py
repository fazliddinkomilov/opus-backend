from django.urls import path

from .views import MeView, MockOTPStartView, MockOTPVerifyView, PasswordLoginView, LogoutView


urlpatterns = [
    path("otp/start/", MockOTPStartView.as_view(), name="mock_otp_start"),
    path("otp/verify/", MockOTPVerifyView.as_view(), name="mock_otp_verify"),
    path("login/", PasswordLoginView.as_view(), name="password_login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
]

