from __future__ import annotations

from pydantic import BaseModel, Field


class SellerAssetUploadRequest(BaseModel):
    seller_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    image_base64: str = Field(min_length=1)


class SellerAssetUploadResponse(BaseModel):
    seller_original_key: str
    buyer_thumbnail_key: str
    width: int
    height: int
    state: str


class OrderHandoffRequest(BaseModel):
    order_id: str = Field(min_length=1)
    seller_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)


class OrderHandoffResponse(BaseModel):
    order_id: str
    status: str
    deliverable_key: str
