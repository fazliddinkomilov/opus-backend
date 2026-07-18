from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from apps.accounts.services import OTPError, start_otp
from apps.accounts.sms import SmsError, normalize_phone


class NormalizePhoneTests(TestCase):
    def test_variants_normalize_to_msisdn(self):
        self.assertEqual(normalize_phone("+998 90 123 45 67"), "998901234567")
        self.assertEqual(normalize_phone("998901234567"), "998901234567")
        self.assertEqual(normalize_phone("901234567"), "998901234567")
        self.assertEqual(normalize_phone("00998901234567"), "998901234567")


@override_settings(MASTERGO_MOCK_OTP=False)
class OtpSmsDeliveryTests(TestCase):
    def setUp(self):
        cache.clear()

    @override_settings(SMS_DRY_RUN=True)
    def test_dry_run_does_not_call_provider_send_over_network(self):
        # ConsoleSmsProvider only logs; start_otp must succeed without raising.
        with patch("apps.accounts.services.random.randint", return_value=4321):
            result = start_otp("+998901112233")
        self.assertEqual(result.phone, "+998901112233")

    @override_settings(SMS_DRY_RUN=False)
    def test_real_send_is_invoked_with_rendered_code(self):
        with patch("apps.accounts.services.random.randint", return_value=4321), patch(
            "apps.accounts.services.send_otp_sms"
        ) as send_mock:
            start_otp("+998901112233")
        send_mock.assert_called_once_with("+998901112233", "4321")

    @override_settings(SMS_DRY_RUN=False)
    def test_send_failure_raises_and_clears_resend_throttle(self):
        with patch("apps.accounts.services.random.randint", return_value=4321), patch(
            "apps.accounts.services.send_otp_sms", side_effect=SmsError("boom")
        ):
            with self.assertRaises(OTPError) as ctx:
                start_otp("+998901112233")
        self.assertEqual(ctx.exception.code, "otp_send_failed")
        # Resend window rolled back so the user can retry immediately.
        self.assertIsNone(cache.get("otp:login:998901112233:resend"))
