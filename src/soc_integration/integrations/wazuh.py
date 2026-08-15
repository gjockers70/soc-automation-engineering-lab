"""Wazuh manager API client."""

from __future__ import annotations

from .base import RetryingClient


class WazuhClient(RetryingClient):
    def __init__(self, base_url: str, username: str, password: str, **kwargs: object) -> None:
        super().__init__("wazuh", base_url, **kwargs)  # type: ignore[arg-type]
        self.username = username
        self.password = password

    async def token(self) -> str:
        response = await self.request(
            "POST", "/security/user/authenticate", auth=(self.username, self.password)
        )
        payload = response.json()
        return str(payload["data"]["token"])

    async def health(self) -> None:
        token = await self.token()
        await self.request("GET", "/manager/status", headers={"Authorization": f"Bearer {token}"})
