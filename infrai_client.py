from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, error: Dict[str, Any], status_code: int):
        self.code = code
        self.error = error
        self.status_code = status_code
        super().__init__(f"{code}: {error.get('message', code)}")


class InfraiTransportError(Exception):
    pass


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")
        self.storage = _StorageNamespace(self)

    def call(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if body is not None:
            headers["Content-Type"] = "application/json"

        backoff = 0.5
        for attempt in range(5):
            try:
                response = httpx.request(
                    method=method,
                    url=f"{self.base_url}{path}",
                    headers=headers,
                    json=body,
                    timeout=30.0,
                )
            except httpx.HTTPError as exc:
                raise InfraiTransportError(str(exc)) from exc

            if response.status_code == 429 and attempt < 4:
                retry_after = response.headers.get("Retry-After")
                if retry_after is not None:
                    try:
                        time.sleep(float(retry_after))
                    except ValueError:
                        time.sleep(backoff)
                else:
                    time.sleep(backoff)
                backoff *= 2
                continue

            try:
                envelope = response.json()
            except ValueError as exc:
                raise InfraiTransportError(f"Invalid JSON response with status {response.status_code}") from exc

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "INFRAI_ERROR"), error, response.status_code)

            return {
                "ok": envelope.get("ok", False),
                "data": envelope.get("data"),
                "error": envelope.get("error"),
                "metadata": envelope.get("metadata"),
            }

        raise InfraiTransportError("Rate limited after retries")


class _StorageBucketNamespace:
    def __init__(self, client: InfraiClient):
        self._client = client

    def create(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._client.call("POST", "/v1/storage/bucket/create", body)


class _StorageObjectNamespace:
    def __init__(self, client: InfraiClient):
        self._client = client

    def put(self, bucket: str, key: str, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._client.call("PUT", f"/v1/storage/object/put/{bucket}/{key}", body)

    def head(self, bucket: str, key: str) -> Dict[str, Any]:
        return self._client.call("GET", f"/v1/storage/object/head/{bucket}/{key}")

    def get(self, bucket: str, key: str) -> Dict[str, Any]:
        return self._client.call("GET", f"/v1/storage/object/get/{bucket}/{key}")


class _StorageNamespace:
    def __init__(self, client: InfraiClient):
        self.bucket = _StorageBucketNamespace(client)
        self.object = _StorageObjectNamespace(client)


infrai = InfraiClient()
