from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SpinResult(BaseModel):
    sliceIndex: int
    label: str
    prize: bool
    allPrizesGone: bool = False


class PrizeStats(BaseModel):
    name: str
    total: int
    remaining: int
    weight: int


class InventoryStats(BaseModel):
    prizes: List[PrizeStats]
    total_spins: int
    total_wins: int
    all_prizes_gone: bool


class SpinResponse(BaseModel):
    id: int
    label: str
    is_prize: bool
    created_at: str

