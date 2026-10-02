from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from infrai_client import InfraiError, infrai
from marketplace_models import OrderHandoffRequest, OrderHandoffResponse, SellerAssetUploadRequest, SellerAssetUploadResponse
from marketplace_pipeline import MarketplaceImageService
from storage_handoff import InfraiStorageHandoff

BUCKET = os.environ.get("MARKETPLACE_BUCKET", "creator-market-assets")

storage = InfraiStorageHandoff(infrai)
service = MarketplaceImageService(storage=storage, bucket=BUCKET)


@asynccontextmanager
async def lifespan(_: FastAPI):
    service.ensure_bucket()
    yield


app = FastAPI(title="Marketplace image handoff", lifespan=lifespan)


@app.post("/seller/assets", response_model=SellerAssetUploadResponse)
def create_seller_asset(request: SellerAssetUploadRequest) -> SellerAssetUploadResponse:
    try:
        return service.upload_seller_asset(request)
    except InfraiError as exc:
        raise HTTPException(status_code=400, detail=exc.error) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/orders/handoff", response_model=OrderHandoffResponse)
def create_order_handoff(request: OrderHandoffRequest) -> OrderHandoffResponse:
    try:
        return service.handoff_order_asset(request)
    except InfraiError as exc:
        raise HTTPException(status_code=400, detail=exc.error) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
