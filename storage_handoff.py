from __future__ import annotations

import base64
from typing import Any


class InfraiStorageHandoff:
    def __init__(self, infrai_client: Any):
        self.infrai = infrai_client

    def ensure_bucket(self, bucket: str) -> None:
        self.infrai.storage.bucket.create({"name": bucket})

    def put_bytes(self, bucket: str, key: str, data: bytes, content_type: str, idempotency_key: str) -> None:
        self.infrai.storage.object.put(
            bucket,
            key,
            {
                "data_base64": base64.b64encode(data).decode("utf-8"),
                "content_type": content_type,
                "idempotency_key": idempotency_key,
            },
        )

    def head_object(self, bucket: str, key: str) -> bool:
        envelope = self.infrai.storage.object.head(bucket, key)
        data = envelope["data"] or {}
        return bool(data.get("found"))

    def get_bytes(self, bucket: str, key: str) -> bytes:
        envelope = self.infrai.storage.object.get(bucket, key)
        data = envelope["data"] or {}
        return base64.b64decode(data["data_base64"])
