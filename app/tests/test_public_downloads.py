"""Public download metadata endpoint."""

import pytest
from django.test import Client


@pytest.mark.django_db
def test_public_downloads_returns_json():
    client = Client()
    response = client.get("/api/public/downloads/")
    assert response.status_code == 200
    data = response.json()
    assert "android_tv_apk_url" in data
    assert isinstance(data["android_tv_apk_url"], str)
