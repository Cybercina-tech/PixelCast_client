import re

from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from django.utils import timezone

from templates.models import Content, Widget, Layer, QRActionLink, QRActionRule, QRScanEvent
from tests.base import BaseAPITestCase


UUID_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


class TemplateEditorSyncTests(BaseAPITestCase):
    def test_activate_on_screen_updates_screen_and_queues_commands(self):
        template = self.create_template(name="Editor Activation Template")
        screen = self.create_screen(name="Lobby Screen")

        cache_key = f"screen_template_{screen.id}"
        cache.set(cache_key, "stale-template", timeout=60)

        url = reverse("template-activate-on-screen", kwargs={"id": str(template.id)})
        response = self.client.post(
            url,
            {"screen_id": str(screen.id), "sync_content": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertTrue(response.data["commands_queued"])
        self.assertIn("screen", response.data)
        self.assertIsNone(cache.get(cache_key))

        screen.refresh_from_db()
        self.assertEqual(screen.active_template_id, template.id)
        self.assertTrue(screen.commands.filter(type="refresh").exists())
        self.assertTrue(screen.commands.filter(type="sync_content").exists())

    def test_template_save_syncs_widget_ids_to_backend_uuid(self):
        template = self.create_template(name="Widget Sync Template", config_json={})

        payload = {
            "config_json": {
                "widgets": [
                    {
                        "id": "widget-local-123",
                        "type": "text",
                        "name": "Headline",
                        "x": "10%",
                        "y": "20%",
                        "width": "30%",
                        "height": "15%",
                        "zIndex": 1,
                        "visible": True,
                        "content": "Hello",
                        "style": {"fontSize": "24px"},
                    }
                ]
            }
        }
        url = reverse("template-detail", kwargs={"id": str(template.id)})
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        template.refresh_from_db()
        self.assertEqual(Widget.objects.filter(layer__template=template).count(), 1)
        synced_widget_id = template.config_json["widgets"][0]["id"]
        self.assertRegex(synced_widget_id, UUID_REGEX)

    def test_template_save_links_content_id_to_synced_widget(self):
        template = self.create_template(name="Content Link Template", config_json={})
        content = Content.objects.create(
            name="Standalone Image",
            type="image",
            file_url="https://example.com/image.jpg",
            widget=None,
            is_active=True,
        )

        payload = {
            "config_json": {
                "widgets": [
                    {
                        "id": "tmp-widget-id",
                        "type": "image",
                        "name": "Image Widget",
                        "x": "5%",
                        "y": "5%",
                        "width": "40%",
                        "height": "40%",
                        "zIndex": 2,
                        "visible": True,
                        "content": "https://example.com/image.jpg",
                        "content_id": str(content.id),
                        "style": {"objectFit": "cover"},
                    }
                ]
            }
        }
        url = reverse("template-detail", kwargs={"id": str(template.id)})
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content.refresh_from_db()
        self.assertIsNotNone(content.widget_id)
        self.assertEqual(content.widget.layer.template_id, template.id)

    def test_template_save_weather_widget_persists_style_in_content_json(self):
        template = self.create_template(name="Weather Sync Template", config_json={})

        payload = {
            "config_json": {
                "widgets": [
                    {
                        "id": "weather-local-001",
                        "type": "weather",
                        "name": "Weather Card",
                        "x": "15%",
                        "y": "10%",
                        "width": "30%",
                        "height": "22%",
                        "zIndex": 3,
                        "visible": True,
                        "content": "Paris,FR",
                        "style": {
                            "units": "celsius",
                            "layout": "extended",
                            "forecastDays": 5,
                        },
                    }
                ]
            }
        }
        url = reverse("template-detail", kwargs={"id": str(template.id)})
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        widget = Widget.objects.get(layer__template=template, type="weather")
        self.assertEqual(widget.content_json.get("units"), "celsius")
        self.assertEqual(widget.content_json.get("layout"), "extended")
        self.assertEqual(widget.content_json.get("location"), "Paris,FR")

    def test_template_save_countdown_widget_persists_style(self):
        template = self.create_template(name="Countdown Sync Template", config_json={})
        payload = {
            "config_json": {
                "widgets": [
                    {
                        "id": "cd-local-001",
                        "type": "countdown",
                        "name": "Sale Ends",
                        "x": "10%",
                        "y": "10%",
                        "width": "40%",
                        "height": "15%",
                        "zIndex": 2,
                        "visible": True,
                        "content": "Spring Sale",
                        "style": {
                            "targetAt": "2030-01-01T12:00:00.000Z",
                            "zeroStateMode": "showMessage",
                            "theme": "urgency",
                            "labels": {"days": "روز", "hours": "ساعت"},
                        },
                    }
                ]
            }
        }
        url = reverse("template-detail", kwargs={"id": str(template.id)})
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        widget = Widget.objects.get(layer__template=template, type="countdown")
        self.assertEqual(widget.content_json.get("theme"), "urgency")
        self.assertEqual(widget.content_json.get("labels", {}).get("days"), "روز")

    def test_template_save_qr_action_creates_qr_link_and_rules(self):
        template = self.create_template(name="QR Sync Template", config_json={})
        payload = {
            "config_json": {
                "widgets": [
                    {
                        "id": "qr-local-001",
                        "type": "qr_action",
                        "name": "QR Action",
                        "x": "20%",
                        "y": "10%",
                        "width": "20%",
                        "height": "30%",
                        "zIndex": 3,
                        "visible": True,
                        "content": "https://example.com/default",
                        "style": {
                            "campaignId": "cmp-42",
                            "defaultUrl": "https://example.com/default",
                            "rules": [
                                {
                                    "name": "Morning",
                                    "priority": 1,
                                    "startHour": 8,
                                    "endHour": 12,
                                    "daysOfWeek": [0, 1, 2, 3, 4, 5, 6],
                                    "targetUrl": "https://example.com/morning",
                                }
                            ],
                        },
                    }
                ]
            }
        }
        url = reverse("template-detail", kwargs={"id": str(template.id)})
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        widget = Widget.objects.get(layer__template=template, type="qr_action")
        link = QRActionLink.objects.get(widget=widget)
        self.assertEqual(link.campaign_id, "cmp-42")
        self.assertEqual(link.rules.count(), 1)

    def test_template_save_album_widget_links_multiple_contents_with_order_and_duration(self):
        template = self.create_template(name="Album Sync Template", config_json={})
        first_content = Content.objects.create(
            name="Album First",
            type="image",
            file_url="https://example.com/album-1.jpg",
            widget=None,
            is_active=True,
        )
        second_content = Content.objects.create(
            name="Album Second",
            type="video",
            file_url="https://example.com/album-2.mp4",
            widget=None,
            is_active=True,
        )

        payload = {
            "config_json": {
                "widgets": [
                    {
                        "id": "album-local-001",
                        "type": "album",
                        "name": "Hero Album",
                        "x": "10%",
                        "y": "8%",
                        "width": "60%",
                        "height": "60%",
                        "zIndex": 1,
                        "visible": True,
                        "content_ids": [str(first_content.id), str(second_content.id)],
                        "playlist_items": [
                            {"content_id": str(first_content.id), "durationSec": 7, "transition": "fade"},
                            {"content_id": str(second_content.id), "durationSec": 15, "transition": "slideLeft"},
                        ],
                        "style": {
                            "transition": "fade",
                            "defaultDurationSec": 10,
                            "gifMode": "autoEnd",
                            "objectFit": "contain",
                        },
                    }
                ]
            }
        }

        url = reverse("template-detail", kwargs={"id": str(template.id)})
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        widget = Widget.objects.get(layer__template=template, type="album")
        self.assertEqual(widget.content_json.get("gifMode"), "autoEnd")
        self.assertEqual(widget.content_json.get("objectFit"), "contain")

        first_content.refresh_from_db()
        second_content.refresh_from_db()

        self.assertEqual(first_content.widget_id, widget.id)
        self.assertEqual(second_content.widget_id, widget.id)
        self.assertEqual(first_content.order, 0)
        self.assertEqual(second_content.order, 1)
        self.assertEqual(first_content.duration, 7.0)
        self.assertEqual(second_content.duration, 15.0)
        self.assertEqual(first_content.content_json.get("transition"), "fade")
        self.assertEqual(second_content.content_json.get("transition"), "slideLeft")


class QRActionFlowTests(BaseAPITestCase):
    def test_qr_action_redirect_resolves_rule_and_logs_scan(self):
        template = self.create_template(name="QR Template")
        layer = Layer.objects.create(
            name="QR Layer",
            template=template,
            width=1920,
            height=1080,
            x=0,
            y=0,
            z_index=0,
        )
        widget = Widget.objects.create(
            name="QR Widget",
            type="qr_action",
            layer=layer,
            x=100,
            y=100,
            width=300,
            height=300,
            content_json={},
        )
        link = QRActionLink.objects.create(
            widget=widget,
            slug="test-qr-link",
            default_url="https://example.com/default",
            campaign_id="cmp-001",
        )
        QRActionRule.objects.create(
            link=link,
            name="All day override",
            priority=1,
            target_url="https://example.com/morning",
            start_hour=0,
            end_hour=23,
            days_of_week=[0, 1, 2, 3, 4, 5, 6],
            is_active=True,
        )

        url = reverse("qr-action-redirect", kwargs={"slug": link.slug})
        response = self.client.get(url, {"screen": "branch-x"}, HTTP_USER_AGENT="pytest-agent/1.0")

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response["Location"], "https://example.com/morning")
        event = QRScanEvent.objects.get(link=link)
        self.assertEqual(event.campaign_id, "cmp-001")
        self.assertEqual(event.source_screen, "branch-x")
        self.assertEqual(event.resolved_url, "https://example.com/morning")

    def test_qr_action_link_analytics_endpoint_returns_totals(self):
        template = self.create_template(name="QR Analytics Template")
        layer = Layer.objects.create(
            name="QR Layer",
            template=template,
            width=1920,
            height=1080,
            x=0,
            y=0,
            z_index=0,
        )
        widget = Widget.objects.create(
            name="QR Widget",
            type="qr_action",
            layer=layer,
            x=10,
            y=10,
            width=320,
            height=320,
            content_json={},
        )
        link = QRActionLink.objects.create(
            widget=widget,
            slug="analytics-link",
            default_url="https://example.com/default",
            campaign_id="cmp-analytics",
        )
        QRScanEvent.objects.create(
            link=link,
            campaign_id="cmp-analytics",
            resolved_url="https://example.com/default",
            created_at=timezone.now(),
        )
        QRScanEvent.objects.create(
            link=link,
            campaign_id="cmp-analytics",
            resolved_url="https://example.com/default",
            created_at=timezone.now(),
        )

        url = reverse("qr-action-link-analytics")
        response = self.client.get(url, {"campaign_id": "cmp-analytics"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_scans"], 2)
