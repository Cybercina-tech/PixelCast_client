import uuid

from django.core.management.base import BaseCommand

from templates.models import Template


class Command(BaseCommand):
    help = (
        "Detect and clean legacy templates that are incompatible with strict "
        "WYSIWYG player rendering."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--action",
            choices=["delete", "deactivate"],
            default="deactivate",
            help="Cleanup action for legacy templates (default: deactivate).",
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Apply changes. Without this flag, command runs in dry-run mode.",
        )

    def handle(self, *args, **options):
        action = options["action"]
        confirm = options["confirm"]

        templates = Template.objects.all().order_by("created_at")
        legacy_templates = []

        for template in templates:
            reasons = self._legacy_reasons(template)
            if reasons:
                legacy_templates.append((template, reasons))

        if not legacy_templates:
            self.stdout.write(self.style.SUCCESS("No legacy templates found."))
            return

        self.stdout.write(
            self.style.WARNING(
                f"Found {len(legacy_templates)} legacy template(s). "
                f"Action={action}, confirm={confirm}"
            )
        )

        for template, reasons in legacy_templates:
            reason_text = "; ".join(reasons)
            self.stdout.write(
                f"- {template.id} | {template.name} | active={template.is_active} | {reason_text}"
            )

        if not confirm:
            self.stdout.write(
                self.style.WARNING(
                    "Dry-run only. Re-run with --confirm to apply changes."
                )
            )
            return

        changed_count = 0
        for template, _ in legacy_templates:
            if action == "delete":
                template.delete()
                changed_count += 1
                continue

            if template.is_active:
                template.is_active = False
                template.save(update_fields=["is_active"])
                changed_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Cleanup completed. Changed {changed_count} template(s)."
            )
        )

    def _legacy_reasons(self, template):
        reasons = []
        cfg = template.config_json

        if not isinstance(cfg, dict):
            return ["config_json is not a JSON object"]

        widgets = cfg.get("widgets")
        if not isinstance(widgets, list):
            return ["config_json.widgets is not a list"]

        for idx, widget in enumerate(widgets):
            if not isinstance(widget, dict):
                reasons.append(f"widget[{idx}] is not an object")
                continue

            widget_id = widget.get("id")
            if not self._is_uuid(widget_id):
                reasons.append(f"widget[{idx}] id is not UUID")

            widget_type = widget.get("type")
            if not widget_type:
                reasons.append(f"widget[{idx}] missing type")

            for key in ("x", "y", "width", "height"):
                if key not in widget:
                    reasons.append(f"widget[{idx}] missing {key}")

        # Preserve order while removing duplicates.
        return list(dict.fromkeys(reasons))

    @staticmethod
    def _is_uuid(value):
        if not value:
            return False
        try:
            uuid.UUID(str(value))
            return True
        except (ValueError, TypeError, AttributeError):
            return False
