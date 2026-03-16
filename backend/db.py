"""
Supabase database helpers.
All DB interaction goes through functions here to keep routes clean.
"""
from __future__ import annotations
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(override=True)

_client: Client | None = None


def get_db() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SECRET"]
        _client = create_client(url, key)
    return _client


# ---------------------------------------------------------------------------
# processed_emails helpers
# ---------------------------------------------------------------------------

def db_list_emails(page: int, limit: int) -> tuple[list[dict], int]:
    """Return (rows, total_count) for a page of processed_emails."""
    db = get_db()
    offset = (page - 1) * limit

    # Total count
    count_result = (
        db.table("processed_emails").select("id", count="exact").execute()
    )
    total = count_result.count or 0

    # Page of rows
    rows = (
        db.table("processed_emails")
        .select("*")
        .order("processed_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
        .data
    )

    # Attach shipment counts
    for row in rows:
        count = (
            db.table("shipments")
            .select("id", count="exact")
            .eq("run_id", row["id"])
            .execute()
            .count
        ) or 0
        row["shipment_count"] = count

    return rows, total


def db_get_email(email_id: str) -> dict | None:
    """Return a single processed_email with nested shipments + requirements."""
    db = get_db()

    result = (
        db.table("processed_emails").select("*").eq("id", email_id).execute()
    )
    if not result.data:
        return None
    row = result.data[0]

    # Fetch shipments
    shipments_result = (
        db.table("shipments").select("*").eq("run_id", email_id).execute()
    )
    shipments = shipments_result.data or []

    # Attach special requirements to each shipment
    for shipment in shipments:
        reqs = (
            db.table("shipment_special_requirements")
            .select("requirement")
            .eq("shipment_id", shipment["id"])
            .execute()
        )
        shipment["special_requirements"] = [r["requirement"] for r in (reqs.data or [])]

    row["shipments"] = shipments
    row["shipment_count"] = len(shipments)
    return row


def db_create_email(record: dict, shipments: list[dict]) -> dict:
    """Insert an email record and its shipments. Returns the full record."""
    db = get_db()

    # Insert email
    inserted = db.table("processed_emails").insert(record).execute()
    email_row = inserted.data[0]
    email_id = email_row["id"]

    # Insert shipments
    for shipment in shipments:
        reqs = shipment.pop("special_requirements", [])
        shipment["run_id"] = email_id
        s_result = db.table("shipments").insert(shipment).execute()
        shipment_id = s_result.data[0]["id"]

        # Insert requirements
        if reqs:
            req_rows = [{"shipment_id": shipment_id, "requirement": r} for r in reqs]
            db.table("shipment_special_requirements").insert(req_rows).execute()

    return db_get_email(email_id)


def db_update_email(email_id: str, fields: dict) -> dict | None:
    """Partial update of processed_email fields."""
    db = get_db()
    db.table("processed_emails").update(fields).eq("id", email_id).execute()
    return db_get_email(email_id)


def db_delete_email(email_id: str) -> None:
    """Delete an email (cascades to shipments + requirements)."""
    db = get_db()
    db.table("processed_emails").delete().eq("id", email_id).execute()


# ---------------------------------------------------------------------------
# shipments helpers
# ---------------------------------------------------------------------------

def db_get_shipment(shipment_id: str) -> dict | None:
    db = get_db()
    result = db.table("shipments").select("*").eq("id", shipment_id).execute()
    if not result.data:
        return None
    shipment = result.data[0]
    reqs = (
        db.table("shipment_special_requirements")
        .select("requirement")
        .eq("shipment_id", shipment_id)
        .execute()
    )
    shipment["special_requirements"] = [r["requirement"] for r in (reqs.data or [])]
    return shipment


def db_update_shipment(shipment_id: str, fields: dict) -> dict | None:
    """Partial update of a shipment, including optional replacement of requirements."""
    db = get_db()
    reqs = fields.pop("special_requirements", None)

    if fields:
        db.table("shipments").update(fields).eq("id", shipment_id).execute()

    if reqs is not None:
        # Replace requirements
        db.table("shipment_special_requirements").delete().eq("shipment_id", shipment_id).execute()
        if reqs:
            req_rows = [{"shipment_id": shipment_id, "requirement": r} for r in reqs]
            db.table("shipment_special_requirements").insert(req_rows).execute()

    return db_get_shipment(shipment_id)


def db_delete_shipment(shipment_id: str) -> None:
    db = get_db()
    db.table("shipments").delete().eq("id", shipment_id).execute()
