"""Concurrent integration health evaluation."""

from __future__ import annotations

import asyncio
import time
from typing import Protocol

from .integrations.base import IntegrationError
from .models import IntegrationHealth


class HealthClient(Protocol):
    async def health(self) -> None: ...


async def check_one(client: HealthClient | None) -> IntegrationHealth:
    if client is None:
        return IntegrationHealth(status="not_configured")
    started = time.perf_counter()
    try:
        await client.health()
    except IntegrationError as exc:
        return IntegrationHealth(
            status="unhealthy",
            latency_ms=round((time.perf_counter() - started) * 1000),
            detail=exc.category,
        )
    return IntegrationHealth(
        status="healthy", latency_ms=round((time.perf_counter() - started) * 1000)
    )


async def integration_health(clients: dict[str, HealthClient | None]) -> dict[str, IntegrationHealth]:
    names = list(clients)
    results = await asyncio.gather(*(check_one(clients[name]) for name in names))
    return dict(zip(names, results, strict=True))
