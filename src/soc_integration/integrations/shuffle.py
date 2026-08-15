"""Shuffle REST client."""

from __future__ import annotations

from .base import RetryingClient


class ShuffleClient(RetryingClient):
    def __init__(self, base_url: str, api_key: str, **kwargs: object) -> None:
        super().__init__("shuffle", base_url, **kwargs)  # type: ignore[arg-type]
        self.headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}

    async def health(self) -> None:
        await self.request("GET", "/api/v1/workflows", headers=self.headers)

    async def workflows(self) -> list[dict]:
        response = await self.request("GET", "/api/v1/workflows", headers=self.headers)
        result = response.json()
        return result if isinstance(result, list) else result.get("workflows", [])

    async def executions(self, workflow_id: str) -> list[dict]:
        response = await self.request(
            "GET", f"/api/v1/workflows/{workflow_id}/executions", headers=self.headers
        )
        result = response.json()
        return result if isinstance(result, list) else result.get("executions", [])

    async def trigger(self, webhook_url: str, webhook_token: str, payload: dict) -> dict:
        response = await self.request(
            "POST",
            webhook_url,
            headers={
                "X-SOC-LAB-TOKEN": webhook_token,
                "Idempotency-Key": str(payload.get("trace_id", "")),
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            retry_safe=False,
        )
        result = response.json()
        return result if isinstance(result, dict) else {}
