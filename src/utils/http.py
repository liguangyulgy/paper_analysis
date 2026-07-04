from __future__ import annotations

import time
import urllib.parse
import urllib.request

try:
    import truststore
except ImportError:  # pragma: no cover - exercised only when optional dependency is absent.
    truststore = None


class HttpClient:
    def __init__(self, *, timeout: float = 30.0, retries: int = 3, delay_seconds: float = 0.34) -> None:
        self.timeout = timeout
        self.retries = retries
        self.delay_seconds = delay_seconds

    def get_text(self, url: str, params: dict[str, object | None]) -> str:
        query = urllib.parse.urlencode(
            {key: value for key, value in params.items() if value is not None}
        )
        full_url = f"{url}?{query}" if query else url
        last_error: Exception | None = None

        for attempt in range(self.retries):
            if attempt > 0:
                time.sleep(self.delay_seconds * attempt)
            try:
                request = urllib.request.Request(
                    full_url,
                    headers={"User-Agent": "paper-analysis/0.1"},
                )
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return response.read().decode("utf-8")
            except Exception as exc:  # pragma: no cover - exact urllib failures vary by platform.
                last_error = exc

        raise RuntimeError(f"HTTP GET failed after {self.retries} attempts: {full_url}") from last_error


def inject_system_truststore() -> bool:
    if truststore is None:
        return False
    truststore.inject_into_ssl()
    return True
