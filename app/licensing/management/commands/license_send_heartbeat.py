"""Send a heartbeat to the operator license gateway (requires activation token)."""

from django.conf import settings
from django.core.management.base import BaseCommand

from licensing.client import LicenseServerError, license_gateway_base_url, post_gateway_heartbeat
from licensing.service import apply_heartbeat_gateway_response, get_or_create_state


class Command(BaseCommand):
    help = "POST /heartbeat/ to LICENSE_GATEWAY_BASE_URL using the stored activation token."

    def handle(self, *args, **options):
        base = license_gateway_base_url()
        state = get_or_create_state()
        token = (state.activation_token or "").strip()
        if not base or not token:
            self.stdout.write(
                self.style.WARNING(
                    "Skipped: set LICENSE_GATEWAY_BASE_URL and activate the installation first."
                )
            )
            return
        try:
            data = post_gateway_heartbeat(
                base,
                token,
                body={
                    "domain": state.activated_domain or "",
                    "app_version": (getattr(settings, "SCREENGRAM_APP_VERSION", None) or "").strip(),
                },
            )
            apply_heartbeat_gateway_response(state, data)
        except LicenseServerError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            raise SystemExit(1) from exc
        self.stdout.write(self.style.SUCCESS("License heartbeat sent."))
