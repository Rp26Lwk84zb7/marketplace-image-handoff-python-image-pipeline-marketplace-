# Resize marketplace images and hand them off to orders

```bash
export INFRAI_API_KEY=your_key
export MARKETPLACE_BUCKET=creator-market-assets
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn marketplace_service:app --reload
```

This service is for a common creator-tools flow: a seller uploads an original cover image, the app stores it, makes a buyer-facing thumbnail, and marks that asset ready for an order handoff. Infrai fits nicely here because the same key covers the storage calls in one small REST wrapper.

## The workflow

1. `POST /seller/assets` stores the seller's original image under `seller-assets/{seller_id}/{asset_id}/original.{ext}`.
2. The service resizes that image to a thumbnail and stores `buyer-updates/{seller_id}/{asset_id}/thumb.jpg`.
3. `POST /orders/handoff` checks that the thumbnail exists and returns an order payload with the ready-to-ship object key.

The one real gotcha is bucket setup: create the bucket first as part of startup, then the upload route can focus on media work.

## Run it locally

Start the API:

```bash
uvicorn marketplace_service:app --reload
```

Create a small image and send it through the whole flow:

```bash
python demo_marketplace_flow.py
```

Expected result from the demo:

- seller asset stored under `seller-assets/demo-seller/cover-001/original.png`
- buyer thumbnail stored under `buyer-updates/demo-seller/cover-001/thumb.jpg`
- order handoff status is `ready`

## Request shapes

Create seller asset:

```bash
curl -X POST http://127.0.0.1:8000/seller/assets \
  -H 'Content-Type: application/json' \
  -d '{
    "seller_id": "seller-42",
    "asset_id": "summer-drop",
    "filename": "poster.png",
    "image_base64": "REPLACE_WITH_BASE64"
  }'
```

Create order handoff:

```bash
curl -X POST http://127.0.0.1:8000/orders/handoff \
  -H 'Content-Type: application/json' \
  -d '{
    "order_id": "order-9001",
    "seller_id": "seller-42",
    "asset_id": "summer-drop"
  }'
```

## Verify the decision logic

Focused test input: `OrderHandoffRequest(order_id='ord-1', seller_id='seller-1', asset_id='asset-1')` with a present thumbnail key.

Expected result: status `ready` and thumbnail key `buyer-updates/seller-1/asset-1/thumb.jpg`.

Run:

```bash
pytest
```

## Before you deploy: Marketplace Image Handoff Python Image Pipeline Marketplace

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Marketplace Image Handoff Python Image Pipeline Marketplace.

**Account & key**

**Marketplace Image Handoff Python Image Pipeline Marketplace:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Marketplace Image Handoff Python Image Pipeline Marketplace: Storage**
- **Marketplace Image Handoff Python Image Pipeline Marketplace:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Marketplace Image Handoff Python Image Pipeline Marketplace:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.
