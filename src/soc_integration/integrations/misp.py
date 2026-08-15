"""MISP REST client."""

from __future__ import annotations

from .base import RetryingClient


class MispClient(RetryingClient):
    def __init__(self, base_url: str, api_key: str, **kwargs: object) -> None:
        super().__init__("misp", base_url, **kwargs)  # type: ignore[arg-type]
        self.headers = {"Authorization": api_key, "Accept": "application/json"}

    async def health(self) -> None:
        await self.request("GET", "/servers/getVersion.json", headers=self.headers)

    async def search(self, value: str, indicator_types: list[str]) -> dict:
        response = await self.request(
            "POST",
            "/attributes/restSearch",
            headers={**self.headers, "Content-Type": "application/json"},
            json={"returnFormat": "json", "value": value, "type": indicator_types},
        )
        return response.json()
