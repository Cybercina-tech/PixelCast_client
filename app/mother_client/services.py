from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone as dj_tz

from signage.models import Screen
from templates.models import Template

try:
    from commands.models import Command
except Exception:  # pragma: no cover
    Command = None  # type: ignore[misc, assignment]

try:
    from media.models import MediaFile
except Exception:  # pragma: no cover
    MediaFile = None  # type: ignore[misc, assignment]


def collect_usage_payload() -> dict:
    """Aggregate simple usage metrics for the mother gateway."""
    active_screens = Screen.objects.filter(is_online=True).count()
    templates_count = Template.objects.count()
    users_count = get_user_model().objects.filter(is_active=True).count()

    commands_sent = 0
    if Command is not None:
        try:
            commands_sent = int(Command.objects.count())
        except Exception:
            commands_sent = 0

    storage_used_mb = 0
    if MediaFile is not None:
        try:
            agg = MediaFile.objects.aggregate(s=Sum("file_size"))
            total_bytes = agg.get("s") or 0
            storage_used_mb = int(total_bytes // (1024 * 1024))
        except Exception:
            storage_used_mb = 0

    now = dj_tz.now()
    return {
        "reported_at": now.isoformat(),
        "active_screens": active_screens,
        "templates_count": templates_count,
        "storage_used_mb": storage_used_mb,
        "commands_sent": commands_sent,
        "users_count": users_count,
    }
