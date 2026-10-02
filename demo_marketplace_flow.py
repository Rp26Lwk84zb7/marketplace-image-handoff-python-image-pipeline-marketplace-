from __future__ import annotations

import base64
import io

from PIL import Image

from marketplace_models import OrderHandoffRequest, SellerAssetUploadRequest
from marketplace_service import service


def make_demo_base64() -> str:
    image = Image.new("RGB", (1200, 900), color=(235, 120, 80))
    out = io.BytesIO()
    image.save(out, format="PNG")
    return base64.b64encode(out.getvalue()).decode("utf-8")


def main() -> None:
    service.ensure_bucket()
    upload = SellerAssetUploadRequest(
        seller_id="demo-seller",
        asset_id="cover-001",
        filename="cover.png",
        image_base64=make_demo_base64(),
    )
    uploaded = service.upload_seller_asset(upload)
    handoff = service.handoff_order_asset(
        OrderHandoffRequest(order_id="order-101", seller_id="demo-seller", asset_id="cover-001")
    )

    print({
        "seller_original_key": uploaded.seller_original_key,
        "buyer_thumbnail_key": uploaded.buyer_thumbnail_key,
        "state": uploaded.state,
        "order_status": handoff.status,
        "deliverable_key": handoff.deliverable_key,
    })


if __name__ == "__main__":
    main()
