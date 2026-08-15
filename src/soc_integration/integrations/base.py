"""Shared timeout, retry, rate-limit, and error behavior."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger("soc.integration.client")


class IntegrationError(RuntimeError):
    def __init__(self, service: str, category: str, status_code: int | None = None) -> None:
        super().__init__(f"{service} integration failed: {category}")
        self.service = service
        self.category = category
        self.status_code = status_code


class RetryingClient:
    retryable_statuses = {429, 502, 503, 504}

    def __init__(
        self,
        service: str,
        base_url: str,
        *,
        timeout: float,
        attempts: int,
        backoff: float,
        verify: bool,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.service = service
        self.attempts = attempts
        self.backoff = backoff
        self.client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"), timeout=timeout, verify=verify, transport=transport
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        retry_safe = bool(kwargs.pop("retry_safe", True))
        max_attempts = self.attempts if retry_safe else 1
        for attempt in range(1, max_attempts + 1):
            try:
                response = await self.client.request(method, path, **kwargs)
            except httpx.TimeoutException as exc:
                if attempt == max_attempts:
                    logger.error(
                        "integration_request_failed service=%s category=timeout attempts=%d",
                        self.service,
                        attempt,
                    )
                    raise IntegrationError(self.service, "timeout") from exc
                logger.warning(
                    "integration_request_retry service=%s category=timeout attempt=%d max_attempts=%d",
                    self.service,
                    attempt,
                    max_attempts,
                )
                await asyncio.sleep(self.backoff * attempt)
                continue
            except httpx.RequestError as exc:
                if attempt == max_attempts:
                    logger.error(
                        "integration_request_failed service=%s category=unavailable attempts=%d",
                        self.service,
                        attempt,
                    )
                    raise IntegrationError(self.service, "unavailable") from exc
                logger.warning(
                    "integration_request_retry service=%s category=unavailable attempt=%d max_attempts=%d",
                    self.service,
                    attempt,
                    max_attempts,
                )
                await asyncio.sleep(self.backoff * attempt)
                continue

            if response.status_code in self.retryable_statuses and attempt < max_attempts:
                retry_after = response.headers.get("Retry-After")
                try:
                    delay = min(float(retry_after), 5.0) if retry_after else self.backoff * attempt
                except ValueError:
                    delay = self.backoff * attempt
                logger.warning(
                    "integration_request_retry service=%s category=http_%d attempt=%d max_attempts=%d delay_seconds=%.3f",
                    self.service,
                    response.status_code,
                    attempt,
                    max_attempts,
                    delay,
                )
                await asyncio.sleep(delay)
                continue
            if response.status_code in {401, 403}:
                logger.error(
                    "integration_request_failed service=%s category=authentication status_code=%d",
                    self.service,
                    response.status_code,
                )
                raise IntegrationError(self.service, "authentication", response.status_code)
            if response.is_error:
                logger.error(
                    "integration_request_failed service=%s category=http_error status_code=%d",
                    self.service,
                    response.status_code,
                )
                raise IntegrationError(self.service, "http_error", response.status_code)
            if attempt > 1:
                logger.info(
                    "integration_request_recovered service=%s attempts=%d",
                    self.service,
                    attempt,
                )
            return response
        raise IntegrationError(self.service, "retry_exhausted")
