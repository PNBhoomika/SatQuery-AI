from pydantic import BaseModel
from typing import Literal


class SearchRequest(BaseModel):
    query: str


class ChangeDetectionRequest(BaseModel):
    tile_id_t1: str
    tile_id_t2: str


class FeedbackRequest(BaseModel):
    alert_id: str
    action: Literal["confirm", "reject"]
    comment: str | None = None