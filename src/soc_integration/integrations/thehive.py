"""TheHive REST client."""

from __future__ import annotations

from .base import RetryingClient


class TheHiveClient(RetryingClient):
    def __init__(self, base_url: str, organisation: str, username: str, password: str, **kwargs: object) -> None:
        super().__init__("thehive", base_url, **kwargs)  # type: ignore[arg-type]
        self.headers = {"X-Organisation": organisation, "Accept": "application/json"}
        self.auth = (username, password)

    async def health(self) -> None:
        await self.request("GET", "/api/v1/status", headers=self.headers, auth=self.auth)

    async def find_cases(self) -> list[dict]:
        response = await self.request(
            "POST",
            "/api/v1/query?name=integration-cases",
            headers={**self.headers, "Content-Type": "application/json"},
            auth=self.auth,
            json={"query": [{"_name": "listCase"}]},
        )
        result = response.json()
        return result if isinstance(result, list) else []

    async def find_case_by_tag(self, tag: str) -> dict | None:
        for case in await self.find_cases():
            if tag in case.get("tags", []):
                return case
        return None

    async def create_case(self, payload: dict) -> dict:
        response = await self.request(
            "POST",
            "/api/v1/case",
            headers={**self.headers, "Content-Type": "application/json"},
            auth=self.auth,
            json=payload,
        )
        result = response.json()
        return result if isinstance(result, dict) else {}

    async def add_observable(self, case_id: str, payload: dict) -> dict:
        response = await self.request(
            "POST", f"/api/v1/case/{case_id}/observable",
            headers={**self.headers, "Content-Type": "application/json"}, auth=self.auth, json=payload,
        )
        result = response.json()
        return result if isinstance(result, dict) else {}

    async def add_comment(self, case_id: str, message: str) -> dict:
        response = await self.request(
            "POST", f"/api/v1/case/{case_id}/comment",
            headers={**self.headers, "Content-Type": "application/json"}, auth=self.auth,
            json={"message": message},
        )
        result = response.json()
        return result if isinstance(result, dict) else {}
