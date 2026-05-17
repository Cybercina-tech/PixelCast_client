"""Lightweight User-Agent parsing for session display (no external dependency)."""

from __future__ import annotations

import re
from typing import Any, TypedDict


class ParsedUserAgent(TypedDict):
    label: str
    browser: str | None
    os: str | None
    device_type: str


def _detect_device_type(ua_lower: str) -> str:
    if 'ipad' in ua_lower or 'tablet' in ua_lower:
        return 'tablet'
    if any(token in ua_lower for token in ('iphone', 'ipod', 'android', 'mobile')):
        return 'mobile'
    return 'desktop'


def _detect_browser(ua_lower: str) -> str | None:
    if 'edg/' in ua_lower or 'edge/' in ua_lower:
        return 'Edge'
    if 'opr/' in ua_lower or 'opera' in ua_lower:
        return 'Opera'
    if 'firefox/' in ua_lower:
        return 'Firefox'
    if 'chrome/' in ua_lower or 'crios/' in ua_lower:
        return 'Chrome'
    if 'safari/' in ua_lower and 'chrome' not in ua_lower and 'chromium' not in ua_lower:
        return 'Safari'
    return None


def _detect_os(ua: str, ua_lower: str) -> str | None:
    if 'windows nt 10' in ua_lower:
        return 'Windows 10/11'
    if 'windows nt 6.3' in ua_lower:
        return 'Windows 8.1'
    if 'windows nt 6.2' in ua_lower:
        return 'Windows 8'
    if 'windows nt 6.1' in ua_lower:
        return 'Windows 7'
    if 'windows' in ua_lower:
        return 'Windows'

    mac_match = re.search(r'Mac OS X (\d+)[._](\d+)', ua, re.I)
    if mac_match:
        major, minor = mac_match.group(1), mac_match.group(2)
        return f'macOS {major}.{minor}'

    ios_match = re.search(r'(?:iPhone|iPad|iPod).*OS (\d+)[._](\d+)', ua, re.I)
    if ios_match:
        return f'iOS {ios_match.group(1)}.{ios_match.group(2)}'

    android_match = re.search(r'Android (\d+(?:\.\d+)?)', ua, re.I)
    if android_match:
        return f'Android {android_match.group(1)}'

    if 'cros' in ua_lower:
        return 'Chrome OS'
    if 'linux' in ua_lower:
        return 'Linux'
    return None


def parse_user_agent(ua: str | None) -> ParsedUserAgent:
    """Return human-readable session metadata from a User-Agent string."""
    raw = (ua or '').strip()
    if not raw:
        return {
            'label': 'Unknown device',
            'browser': None,
            'os': None,
            'device_type': 'desktop',
        }

    ua_lower = raw.lower()
    device_type = _detect_device_type(ua_lower)
    browser = _detect_browser(ua_lower)
    os_name = _detect_os(raw, ua_lower)

    if browser and os_name:
        label = f'{browser} on {os_name}'
    elif browser:
        label = browser
    elif os_name:
        label = os_name
    else:
        label = 'Unknown device'

    return {
        'label': label,
        'browser': browser,
        'os': os_name,
        'device_type': device_type,
    }


def session_device_fields(client_ua: str | None) -> dict[str, Any]:
    """Map stored client_ua claim to API session display fields."""
    parsed = parse_user_agent(client_ua)
    return {
        'device': parsed['label'],
        'browser': parsed['browser'],
        'os': parsed['os'],
        'device_type': parsed['device_type'],
    }
