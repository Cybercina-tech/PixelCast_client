"""Classify SMTP / network errors for API responses and audit."""
from __future__ import annotations

import socket
import ssl

try:
    import smtplib
except ImportError:  # pragma: no cover
    smtplib = None


def classify_email_send_error(exc: BaseException) -> tuple[str, str]:
    """
    Return (error_code, safe_message) for clients.
    Codes: auth, tls, network, timeout, smtp, validation, unknown
    """
    msg = str(exc).strip() or type(exc).__name__
    if isinstance(exc, ValueError):
        return 'validation', msg
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return 'timeout', msg
    if isinstance(exc, (ssl.SSLError, ssl.CertificateError)):
        return 'tls', msg
    if isinstance(exc, (ConnectionRefusedError, ConnectionResetError, BrokenPipeError, OSError)):
        if 'timed out' in msg.lower():
            return 'timeout', msg
        return 'network', msg
    if smtplib and isinstance(exc, smtplib.SMTPAuthenticationError):
        return 'auth', msg
    if smtplib and isinstance(exc, smtplib.SMTPException):
        return 'smtp', msg
    low = msg.lower()
    if 'authentication' in low or '535' in low or '534' in low:
        return 'auth', msg
    if 'tls' in low or 'ssl' in low or 'starttls' in low:
        return 'tls', msg
    return 'unknown', msg
