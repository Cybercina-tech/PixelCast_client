import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from rest_framework.test import APIClient

from licensing.client import LicenseServerError
from licensing.models import LicenseState
from licensing.service import activate_license, validate_license

User = get_user_model()


@override_settings(
    LICENSE_ENFORCEMENT_ENABLED=True,
    LICENSE_OFFLINE_GRACE_HOURS=72,
    LICENSE_CACHE_TTL_SECONDS=1,
    LICENSE_SERVER_URL="https://license.example.test/validate",
)
class LicensingServiceTests(TestCase):
    def setUp(self):
        os.environ["PIXELCAST_SIGNAGE_INSTALLED"] = "true"
        self.state = LicenseState.get_solo()
        self.state.purchase_code = "11111111-2222-3333-4444-555555555555"
        self.state.activated_domain = "example.com"
        self.state.save()

    @patch("licensing.service.post_license_validation")
    def test_active_license_from_server(self, mock_validate):
        mock_validate.return_value = (True, {"status": "active"})
        decision = validate_license(force=True)
        self.assertTrue(decision.allow)
        self.assertEqual(decision.status, LicenseState.STATUS_ACTIVE)

    @patch("licensing.service.post_license_validation")
    def test_invalid_license_from_server(self, mock_validate):
        mock_validate.return_value = (False, {"status": "invalid", "message": "Invalid"})
        decision = validate_license(force=True)
        self.assertFalse(decision.allow)
        self.assertEqual(decision.status, LicenseState.STATUS_INVALID)

    @patch("licensing.service.post_license_validation")
    def test_server_down_uses_grace_after_success(self, mock_validate):
        mock_validate.return_value = (True, {"status": "active"})
        first = validate_license(force=True)
        self.assertTrue(first.allow)

        mock_validate.side_effect = LicenseServerError("down")
        second = validate_license(force=True)
        self.assertTrue(second.allow)
        self.assertEqual(second.status, LicenseState.STATUS_GRACE)

    @patch("licensing.service.post_license_validation")
    def test_product_id_env_first_then_db(self, mock_validate):
        mock_validate.return_value = (True, {"status": "active"})
        os.environ["CODECANYON_PRODUCT_ID"] = "12345"
        decision = activate_license("11111111-2222-3333-4444-555555555555", "example.com", "77777")
        self.assertTrue(decision.allow)
        state = LicenseState.get_solo()
        self.assertEqual(state.codecanyon_product_id_override, "77777")


@override_settings(
    LICENSE_ENFORCEMENT_ENABLED=True,
    LICENSE_OFFLINE_GRACE_HOURS=72,
    LICENSE_SERVER_URL="https://license.example.test/validate",
)
class LicensingMiddlewareTests(TestCase):
    def setUp(self):
        os.environ["PIXELCAST_SIGNAGE_INSTALLED"] = "true"
        self.client = Client()
        self.api_client = APIClient()
        self.user = User.objects.create_user(
            username="dev1",
            email="dev1@example.com",
            password="testpass123",
            role="Developer",
            organization_name="TestOrg",
        )
        self.client.force_login(self.user)
        self.api_client.force_authenticate(user=self.user)
        LicenseState.get_solo()

    @patch("licensing.middleware.validate_license")
    def test_protected_api_denied_when_invalid(self, mock_decision):
        from licensing.service import LicenseDecision

        mock_decision.return_value = LicenseDecision(
            allow=False,
            status="invalid",
            error_code="license_invalid",
            message="License invalid",
        )
        response = self.client.get("/api/users/me/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json().get("error"), "license_invalid")

    @patch("licensing.service.validate_license")
    def test_license_endpoints_are_exempt(self, mock_decision):
        response = self.api_client.get("/api/license/status/")
        # Should not be blocked by middleware; view itself can respond.
        self.assertNotEqual(response.status_code, 403)
