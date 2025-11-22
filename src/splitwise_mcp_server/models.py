"""Data models for Splitwise entities."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExpenseUser:
    """User split information for an expense."""
    user_id: int
    paid_share: str  # Decimal as string
    owed_share: str  # Decimal as string
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None


@dataclass
class ResolutionMatch:
    """Result from entity resolution."""
    id: int
    name: str
    match_score: float  # 0-100
    additional_info: dict  # Extra context (email, balance, etc.)
