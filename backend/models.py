from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Shipment special requirements
# ---------------------------------------------------------------------------
class SpecialRequirement(BaseModel):
    id: str
    shipment_id: str
    requirement: str


# ---------------------------------------------------------------------------
# Shipment
# ---------------------------------------------------------------------------
class Shipment(BaseModel):
    id: str
    run_id: str
    transport_mode: Optional[str] = None
    incoterm: Optional[str] = None
    origin_city: str
    origin_country: str
    origin_address: Optional[str] = None
    dest_city: str
    dest_country: str
    dest_address: Optional[str] = None
    cargo_description: Optional[str] = None
    weight_kg: Optional[float] = None
    volume_cbm: Optional[float] = None
    container_type: Optional[str] = None
    container_count: Optional[int] = None
    piece_count: Optional[int] = None
    special_requirements: list[str] = []


class ShipmentUpdate(BaseModel):
    transport_mode: Optional[str] = None
    incoterm: Optional[str] = None
    origin_city: Optional[str] = None
    origin_country: Optional[str] = None
    origin_address: Optional[str] = None
    dest_city: Optional[str] = None
    dest_country: Optional[str] = None
    dest_address: Optional[str] = None
    cargo_description: Optional[str] = None
    weight_kg: Optional[float] = None
    volume_cbm: Optional[float] = None
    container_type: Optional[str] = None
    container_count: Optional[int] = None
    piece_count: Optional[int] = None
    special_requirements: Optional[list[str]] = None


# ---------------------------------------------------------------------------
# ProcessedEmail (summary — used in list views)
# ---------------------------------------------------------------------------
class ProcessedEmailSummary(BaseModel):
    id: str
    filename: str
    processed_at: datetime
    model: str
    input_tokens: int
    output_tokens: int
    sender_name: str
    sender_email: str
    sender_company: Optional[str] = None
    sender_phone: Optional[str] = None
    shipment_count: int = 0


# ---------------------------------------------------------------------------
# ProcessedEmail (full — includes nested shipments)
# ---------------------------------------------------------------------------
class ProcessedEmail(ProcessedEmailSummary):
    raw_email: str
    shipments: list[Shipment] = []


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------
class ProcessEmailRequest(BaseModel):
    raw_email: str
    filename: str = "manual_entry"


class ProcessedEmailUpdate(BaseModel):
    filename: Optional[str] = None
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None
    sender_company: Optional[str] = None
    sender_phone: Optional[str] = None


# ---------------------------------------------------------------------------
# Paginated response
# ---------------------------------------------------------------------------
class PaginatedEmails(BaseModel):
    data: list[ProcessedEmailSummary]
    total: int
    page: int
    limit: int
    total_pages: int
