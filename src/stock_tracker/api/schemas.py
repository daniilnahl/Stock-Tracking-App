"""Typed HTTP documents; services do not depend on these Pydantic models."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


DecimalText = Annotated[str, Field(
    pattern=r"^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$",
    description="Exact finite Decimal text, including scale/exponent; no float conversion.",
    examples=["120.000", "0", "1E-20"],
)]


class WireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class HealthResponse(WireModel):
    status: Literal["ok"]


class ErrorDetail(WireModel):
    code: str
    message: str


class ErrorResponse(WireModel):
    error: ErrorDetail


class StockResponse(WireModel):
    symbol: str
    name: str | None
    exchange: str | None


class SavedProvenance(WireModel):
    source: None
    observed_at: None
    retrieved_at: None
    freshness: Literal["unknown"]


class SavedMetadata(WireModel):
    """Opaque saved text; currency cannot establish cost/quote provenance."""

    sector: str | None
    country: str | None
    currency: str | None
    market_cap: str | None
    price_1d: str | None
    price_5d: str | None
    price_30d: str | None
    price_3m: str | None
    price_6m: str | None
    price_1y: str | None
    price_3y: str | None
    price_5y: str | None


class SnapshotResponse(WireModel):
    cost_basis: DecimalText = Field(description="Currency amount; currency provenance unknown.")
    market_value: DecimalText | None = Field(description="Currency amount, unavailable when quote is missing.")
    unrealized_pnl: DecimalText | None = Field(description="Currency amount, never an inferred USD amount.")
    unrealized_return: DecimalText | None = Field(description="Dimensionless ratio, not percentage points.")


class EntryResponse(WireModel):
    ordinal: int = Field(ge=0, description="Request-local zero-based row, not a permanent identity.")
    stock: StockResponse
    quantity: DecimalText = Field(description="Shares, including fractional shares.")
    average_cost: DecimalText | None = Field(description="Currency per share; null denotes unowned zero quantity.")
    current_price: DecimalText | None = Field(description="Saved currency per share, freshness unknown; zero differs from null.")
    metadata: SavedMetadata
    snapshot: SnapshotResponse | None


class WatchlistResponse(WireModel):
    namespace: Literal["menu_watchlist", "daniils_stock_method"]
    name: str
    observation: Literal["saved"]
    provenance: SavedProvenance
    entries: list[EntryResponse]


class HistoryProvenance(WireModel):
    source: Literal["fmp"] | None
    observed_at: None
    retrieved_at: None
    currency: None
    freshness: Literal["accepted_cache_policy", "unknown"]


class BarResponse(WireModel):
    symbol: str
    date: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", description="Trading-session label, not a UTC timestamp.")
    open: DecimalText = Field(description="Raw currency per share, currency unknown.")
    high: DecimalText = Field(description="Raw currency per share, currency unknown.")
    low: DecimalText = Field(description="Raw currency per share, currency unknown.")
    close: DecimalText = Field(description="Raw currency per share, currency unknown.")
    adjusted_close: None
    volume: int | None = Field(ge=0, le=9223372036854775807, description="Shares when available.")


class HistoryResponse(WireModel):
    stock: StockResponse
    ordinal: int = Field(ge=0)
    start: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", description="Resolved inclusive requested ISO date.")
    end: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", description="Resolved inclusive requested ISO date.")
    price_basis: Literal["raw"]
    provenance: HistoryProvenance
    bars: list[BarResponse]
