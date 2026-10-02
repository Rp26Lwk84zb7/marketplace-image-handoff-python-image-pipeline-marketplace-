import base64
import io

from PIL import Image

from marketplace_models import OrderHandoffRequest, SellerAssetUploadRequest
from marketplace_pipeline import MarketplaceImageService


class FakeStorage:
    def __init__(self):
        self.created_buckets = []
        self.objects = {}

    def ensure_bucket(self, bucket: str) -> None:
        self.created_buckets.append(bucket)

    def put_bytes(self, bucket: str, key: str, data: bytes, content_type: str, idempotency_key: str) -> None:
        self.objects[(bucket, key)] = {
            "data": data,
            "content_type": content_type,
            "idempotency_key": idempotency_key,
        }

    def head_object(self, bucket: str, key: str) -> bool:
        return (bucket, key) in self.objects


def make_image_base64(size=(900, 600)) -> str:
    image = Image.new("RGB", size, color=(50, 100, 150))
    out = io.BytesIO()
    image.save(out, format="PNG")
    return base64.b64encode(out.getvalue()).decode("utf-8")


def test_upload_creates_original_and_thumbnail_then_handoff_is_ready():
    storage = FakeStorage()
    service = MarketplaceImageService(storage=storage, bucket="market-bucket")

    result = service.upload_seller_asset(
        SellerAssetUploadRequest(
            seller_id="seller-1",
            asset_id="asset-1",
            filename="cover.png",
            image_base64=make_image_base64(),
        )
    )

    assert result.seller_original_key == "seller-assets/seller-1/asset-1/original.png"
    assert result.buyer_thumbnail_key == "buyer-updates/seller-1/asset-1/thumb.jpg"
    assert result.state == "buyer_update_ready"

    handoff = service.handoff_order_asset(
        OrderHandoffRequest(order_id="ord-1", seller_id="seller-1", asset_id="asset-1")
    )

    assert handoff.status == "ready"
    assert handoff.deliverable_key == "buyer-updates/seller-1/asset-1/thumb.jpg"
