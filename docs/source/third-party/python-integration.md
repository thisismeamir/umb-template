# Python Client Integration

This chapter provides a complete, copy-pasteable Python client built on `httpx` for integrating UMB into **FCCAnalyses**, Jupyter notebooks, or automated data-processing pipelines.

## Reusable `UMBClient` with Auto-Refresh & Cursor Pagination

```python
from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

import httpx


class UMBClient:
    """Thin, production-ready third-party client for UMB /api/v1."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        *,
        username: str | None = None,
        password: str | None = None,
        timeout_s: float = 30.0,
    ) -> None:
        self._api = base_url.rstrip("/") + "/api/v1"
        self._client = httpx.Client(timeout=timeout_s)
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        if username and password:
            self.login(username, password)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> UMBClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def login(self, username: str, password: str) -> None:
        resp = self._client.post(
            f"{self._api}/auth/login",
            json={"username": username, "password": password},
        )
        resp.raise_for_status()
        tokens = resp.json()
        self._access_token = tokens["accessToken"]
        self._refresh_token = tokens["refreshToken"]

    def _refresh(self) -> bool:
        if not self._refresh_token:
            return False
        resp = self._client.post(
            f"{self._api}/auth/refresh",
            json={"refreshToken": self._refresh_token},
        )
        if resp.status_code != 200:
            return False
        tokens = resp.json()
        self._access_token = tokens["accessToken"]
        self._refresh_token = tokens["refreshToken"]
        return True

    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        headers = dict(kwargs.pop("headers", {}))
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        resp = self._client.request(method, f"{self._api}{path}", headers=headers, **kwargs)
        if resp.status_code == 401 and self._refresh():
            headers["Authorization"] = f"Bearer {self._access_token}"
            resp = self._client.request(method, f"{self._api}{path}", headers=headers, **kwargs)
        resp.raise_for_status()
        return resp

    def iter_entities(
        self, query: dict[str, Any], *, page_size: int = 100
    ) -> Iterator[dict[str, Any]]:
        """Stream all matching entities using cursor pagination."""
        cursor: str | None = None
        while True:
            payload = dict(query)
            payload["page"] = {"size": page_size, **({"cursor": cursor} if cursor else {})}
            data = self.request("POST", "/entity/query", json=payload).json()
            if not data["validationResult"]["valid"]:
                raise ValueError(data["validationResult"]["errors"])
            for row in data.get("entities") or []:
                yield row
            if not data.get("hasMore") or not data.get("nextCursor"):
                break
            cursor = data["nextCursor"]

    def export_text(self, query: dict[str, Any], fmt: str = "yaml") -> str:
        return self.request("POST", f"/export/{fmt}", json=query).text

    def run_job_and_wait(
        self,
        task_type: str,
        payload: dict[str, Any],
        *,
        poll_interval_s: float = 1.0,
        timeout_s: float = 300.0,
    ) -> Any:
        """Submit a Redis-backed async job and block until done or failed."""
        rec = self.request(
            "POST",
            "/jobs/",
            json={"taskType": task_type, "payload": payload},
        ).json()
        job_id = rec["id"]
        deadline = time.monotonic() + timeout_s

        while time.monotonic() < deadline:
            status_rec = self.request("GET", f"/jobs/{job_id}").json()
            state = status_rec["status"]
            if state == "done":
                return self.request("GET", f"/jobs/{job_id}/result").json()["result"]
            if state == "failed":
                raise RuntimeError(f"Job {job_id} failed: {status_rec.get('error')}")
            time.sleep(poll_interval_s)
        raise TimeoutError(f"Job {job_id} did not finish within {timeout_s}s")
```

## Example 1: Generating an FCCAnalyses `processList`

```python
with UMBClient("http://localhost:8000") as umb:
    yaml_config = umb.export_text(
        {
            "entry_type": "collision",
            "where": {"ecm": "=240"},
            "take": {"name": {}, "process": {}, "ecm": {}, "cross_section_pb": {}},
        },
        fmt="yaml",
    )
    with open("processList_240GeV.yaml", "w", encoding="utf-8") as fh:
        fh.write(yaml_config)
```

## Example 2: Loading into Pandas & Running Analytics

```python
import pandas as pd

with UMBClient("http://localhost:8000") as umb:
    rows = list(
        umb.iter_entities(
            {
                "entry_type": "collision",
                "take": {"name": {}, "process": {}, "ecm": {}, "cross_section_pb": {}},
                "sort": {"by": {"ecm": {}}, "order": "asc"},
            },
            page_size=250,
        )
    )
    df = pd.json_normalize([r["metadata"] for r in rows])
    print(df.head())

    # Server-side cohort comparison (240 GeV vs 365 GeV)
    delta = umb.request(
        "POST",
        "/analytics/compare",
        json={
            "groupA": {"entry_type": "collision", "where": {"ecm": "=240"}},
            "groupB": {"entry_type": "collision", "where": {"ecm": "=365"}},
            "metrics": [{"cross_section_pb": {}}],
        },
    ).json()
    print(delta)
```

## Example 3: Offloading Large Exports to the Redis Worker

```python
with UMBClient("http://localhost:8000", username="amir", password="secret") as umb:
    result = umb.run_job_and_wait(
        "export",
        {
            "format": "csv",
            "query": {"entry_type": "collision", "contains": {"campaign": {}}},
        },
    )
    with open(result["filename"], "w", encoding="utf-8") as fh:
        fh.write(result["content"])
```
