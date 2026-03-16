"""
Freight RFQ — CRUD API
======================
FastAPI backend for storing and managing processed email extractions.

Routes:
  GET    /emails               paginated list (summary)
  POST   /emails               process raw email text → extract → save
  GET    /emails/{id}          full record with shipments
  PATCH  /emails/{id}          update sender / filename fields
  DELETE /emails/{id}          delete email + cascaded shipments

  PATCH  /shipments/{id}       update shipment fields
  DELETE /shipments/{id}       delete single shipment

Run:
  uvicorn main:app --reload --port 8000
"""

import os
import math
from dotenv import load_dotenv

load_dotenv(override=True)

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from models import (
    PaginatedEmails,
    ProcessedEmail,
    ProcessedEmailUpdate,
    ProcessEmailRequest,
    Shipment,
    ShipmentUpdate,
)
from db import (
    db_list_emails,
    db_get_email,
    db_create_email,
    db_update_email,
    db_delete_email,
    db_get_shipment,
    db_update_shipment,
    db_delete_shipment,
)
from extract import extract_rfq, MODEL

app = FastAPI(title="Freight RFQ API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single shared OpenAI client
_openai_client: OpenAI | None = None


def get_openai() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _openai_client


# ---------------------------------------------------------------------------
# processed_emails routes
# ---------------------------------------------------------------------------

@app.get("/emails", response_model=PaginatedEmails)
def list_emails(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=5, ge=1, le=100),
):
    """Return a paginated list of processed emails (summary, no raw text)."""
    rows, total = db_list_emails(page, limit)
    return {
        "data": rows,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": max(1, math.ceil(total / limit)),
    }


@app.post("/emails", response_model=ProcessedEmail, status_code=201)
def process_email(body: ProcessEmailRequest):
    """
    Submit raw email text. Runs LLM extraction, saves to DB, returns full record.
    """
    client = get_openai()
    try:
        result, usage = extract_rfq(client, body.raw_email, body.filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    sender = result["sender"]
    email_record = {
        "filename": body.filename,
        "raw_email": body.raw_email,
        "model": MODEL,
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "sender_name": sender["name"],
        "sender_email": sender["email"],
        "sender_company": sender.get("company"),
        "sender_phone": sender.get("phone"),
    }

    # Convert extracted shipments to flat DB rows
    shipment_rows = []
    for s in result.get("shipments", []):
        cargo = s.get("cargo") or {}
        shipment_rows.append({
            "transport_mode": s.get("transport_mode"),
            "incoterm": s.get("incoterm"),
            "origin_city": s["origin"]["city"],
            "origin_country": s["origin"]["country"],
            "origin_address": s["origin"].get("address"),
            "dest_city": s["destination"]["city"],
            "dest_country": s["destination"]["country"],
            "dest_address": s["destination"].get("address"),
            "cargo_description": cargo.get("description"),
            "weight_kg": cargo.get("weight_kg"),
            "volume_cbm": cargo.get("volume_cbm"),
            "container_type": cargo.get("container_type"),
            "container_count": cargo.get("container_count"),
            "piece_count": cargo.get("piece_count"),
            "special_requirements": s.get("special_requirements", []),
        })

    saved = db_create_email(email_record, shipment_rows)
    return saved


@app.get("/emails/{email_id}", response_model=ProcessedEmail)
def get_email(email_id: str):
    """Return a single processed email with all shipments."""
    row = db_get_email(email_id)
    if not row:
        raise HTTPException(status_code=404, detail="Email not found")
    return row


@app.patch("/emails/{email_id}", response_model=ProcessedEmail)
def update_email(email_id: str, body: ProcessedEmailUpdate):
    """Update sender/filename fields on a processed email."""
    fields = body.model_dump(exclude_none=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields provided to update")
    row = db_update_email(email_id, fields)
    if not row:
        raise HTTPException(status_code=404, detail="Email not found")
    return row


@app.delete("/emails/{email_id}", status_code=204)
def delete_email(email_id: str):
    """Delete a processed email and all its shipments."""
    if not db_get_email(email_id):
        raise HTTPException(status_code=404, detail="Email not found")
    db_delete_email(email_id)


# ---------------------------------------------------------------------------
# shipments routes
# ---------------------------------------------------------------------------

@app.patch("/shipments/{shipment_id}", response_model=Shipment)
def update_shipment(shipment_id: str, body: ShipmentUpdate):
    """Update fields on a single shipment."""
    fields = body.model_dump(exclude_none=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields provided to update")
    row = db_update_shipment(shipment_id, fields)
    if not row:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return row


@app.delete("/shipments/{shipment_id}", status_code=204)
def delete_shipment(shipment_id: str):
    """Delete a single shipment."""
    if not db_get_shipment(shipment_id):
        raise HTTPException(status_code=404, detail="Shipment not found")
    db_delete_shipment(shipment_id)
