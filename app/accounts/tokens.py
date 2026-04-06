"""Custom SimpleJWT refresh tokens with a `role` claim (copied to access tokens)."""

from __future__ import annotations

import uuid
from typing import Any

from rest_framework_simplejwt.tokens import RefreshToken


class ScreenGramRefreshToken(RefreshToken):
    """Refresh (and derived access) tokens include the user's current `role`."""

    @classmethod
    def for_user(
        cls,
        user: Any,
        impersonator_id: Any | None = None,
        *,
        client_ua: str = '',
        client_ip: str = '',
    ) -> 'ScreenGramRefreshToken':
        token = super().for_user(user)
        token['role'] = user.role
        token['sid'] = str(uuid.uuid4())
        if client_ua:
            token['client_ua'] = str(client_ua)[:512]
        if client_ip:
            token['client_ip'] = str(client_ip)[:128]
        if impersonator_id is not None:
            token['impersonator_id'] = str(impersonator_id)
        return token

    @property
    def access_token(self):
        access = super().access_token
        if 'impersonator_id' in self:
            access['impersonator_id'] = self['impersonator_id']
        for key in ('sid', 'client_ua', 'client_ip'):
            if key in self:
                access[key] = self[key]
        return access
