from __future__ import annotations

import base64
import io
from typing import Protocol, Tuple

from PIL import Image

from marketplace_models import OrderHandoffRequest, OrderHandoffResponse, SellerAssetUploadRequest, SellerAssetUploadResponse


class StoragePort(Protocol):
    def ensure_bucket(self, bucket: str) -> None:
        ...

    def put_bytes(self, bucket: str, key: str, data: bytes, content_type: str, idempotency_key: str) -> None:
        ...

    def head_object(self, bucket: str, key: str) -> bool:
        ...


class MarketplaceImageService:
    def __init__(self, storage: StoragePort, bucket: str):
        self.storage = storage
        self.bucket = bucket

    def ensure_bucket(self) -> None:
        self.storage.ensure_bucket(self.bucket)

    def upload_seller_asset(self, request: SellerAssetUploadRequest) -> SellerAssetUploadResponse:
        raw_bytes = base64.b64decode(request.image_base64)
        source_image = Image.open(io.BytesIO(raw_bytes))
        width, height = source_image.size
        ext = _normalized_extension(request.filename)
        original_content_type = _content_type_for_extension(ext)

        original_key = f"seller-assets/{request.seller_id}/{request.asset_id}/original.{ext}"
        thumb_key = f"buyer-updates/{request.seller_id}/{request.asset_id}/thumb.jpg"

        self.storage.put_bytes(
            self.bucket,
            original_key,
            raw_bytes,
            original_content_type,
            idempotency_key=f"seller-asset:{request.seller_id}:{request.asset_id}:original",
        )

        thumb_bytes = render_thumbnail(raw_bytes, size=(480, 480))
        self.storage.put_bytes(
            self.bucket,
            thumb_key,
            thumb_bytes,
            "image/jpeg",
            idempotency_key=f"seller-asset:{request.seller_id}:{request.asset_id}:thumb",
        )

        return SellerAssetUploadResponse(
            seller_original_key=original_key,
            buyer_thumbnail_key=thumb_key,
            width=width,
            height=height,
            state="buyer_update_ready",
        )

    def handoff_order_asset(self, request: OrderHandoffRequest) -> OrderHandoffResponse:
        thumb_key = f"buyer-updates/{request.seller_id}/{request.asset_id}/thumb.jpg"
        if not self.storage.head_object(self.bucket, thumb_key):
            raise ValueError("Buyer thumbnail is not ready yet")
        return OrderHandoffResponse(
            order_id=request.order_id,
            status="ready",
            deliverable_key=thumb_key,
        )


def render_thumbnail(image_bytes: bytes, size: Tuple[int, int]) -> bytes:
    source = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    source.thumbnail(size)
    canvas = Image.new("RGB", size, "white")
    left = (size[0] - source.width) // 2
    top = (size[1] - source.height) // 2
    canvas.paste(source, (left, top))
    out = io.BytesIO()
    canvas.save(out, format="JPEG", quality=88)
    return out.getvalue()


def _normalized_extension(filename: str) -> str:
    if "." not in filename:
        return "png"
    ext = filename.rsplit(".", 1)[1].lower()
    if ext in {"jpg", "jpeg"}:
        return "jpg"
    if ext == "png":
        return "png"
    return "png"


def _content_type_for_extension(ext: str) -> str:
    if ext == "jpg":
        return "image/jpeg"
    return "image/png"
