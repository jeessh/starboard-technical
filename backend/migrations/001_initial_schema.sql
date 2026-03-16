-- Migration: 001_initial_schema
-- Description: Initial schema for storing RFQ email extraction outputs

-- Enable UUID generation
create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- processed_emails
-- One row per email processed. Stores the source email, sender contact info,
-- and token usage metadata for cost tracking.
-- ---------------------------------------------------------------------------
create table processed_emails (
    id              uuid primary key default gen_random_uuid(),
    filename        text not null,
    raw_email       text not null,
    processed_at    timestamptz not null default now(),
    model           text not null,
    input_tokens    integer not null default 0,
    output_tokens   integer not null default 0,

    -- Sender fields inlined (always 1:1 with a run)
    sender_name     text not null,
    sender_email    text not null,
    sender_company  text,
    sender_phone    text
);

comment on table processed_emails is
    'One row per email processed. Tracks source email, sender, and LLM token costs.';
comment on column processed_emails.filename      is 'Original .txt file name (e.g. 01_yantian_to_chicago_fcl.txt)';
comment on column processed_emails.raw_email     is 'Full plaintext content of the email that was processed';
comment on column processed_emails.model         is 'OpenAI model used for extraction (e.g. gpt-4o-mini)';
comment on column processed_emails.input_tokens  is 'Prompt tokens consumed for this run';
comment on column processed_emails.output_tokens is 'Completion tokens consumed for this run';


-- ---------------------------------------------------------------------------
-- shipments
-- One row per shipment extracted from an email.
-- A single email can produce multiple rows (multiple routes or transport modes).
-- Origin/destination fields are kept flat for easy querying.
-- ---------------------------------------------------------------------------
create table shipments (
    id                  uuid primary key default gen_random_uuid(),
    run_id              uuid not null references processed_emails (id) on delete cascade,

    -- Transport
    transport_mode      text check (transport_mode in ('ocean_fcl', 'ocean_lcl', 'air')),
    incoterm            text,

    -- Origin
    origin_city         text not null,
    origin_country      text not null,
    origin_address      text,

    -- Destination
    dest_city           text not null,
    dest_country        text not null,
    dest_address        text,

    -- Cargo
    cargo_description   text,
    weight_kg           numeric,
    volume_cbm          numeric,
    container_type      text,
    container_count     integer,
    piece_count         integer
);

comment on table shipments is
    'One row per shipment request extracted from an email.';
comment on column shipments.run_id          is 'The extraction run this shipment belongs to';
comment on column shipments.transport_mode  is 'ocean_fcl | ocean_lcl | air';
comment on column shipments.origin_address  is 'Full street address if door pickup was requested';
comment on column shipments.dest_address    is 'Full street address if door delivery was requested';
comment on column shipments.weight_kg       is 'Gross weight in kilograms (converted from source unit)';
comment on column shipments.volume_cbm      is 'Volume in cubic meters / CBM (converted from source unit)';


-- ---------------------------------------------------------------------------
-- shipment_special_requirements
-- Normalised storage for the special_requirements[] array.
-- Each element in the array becomes one row.
-- ---------------------------------------------------------------------------
create table shipment_special_requirements (
    id              uuid primary key default gen_random_uuid(),
    shipment_id     uuid not null references shipments (id) on delete cascade,
    requirement     text not null
);

comment on table shipment_special_requirements is
    'Each row is one entry from the special_requirements array for a shipment.';


-- ---------------------------------------------------------------------------
-- Indexes for common query patterns
-- ---------------------------------------------------------------------------

-- Look up all shipments for a run
create index idx_shipments_run_id
    on shipments (run_id);

-- Look up all requirements for a shipment
create index idx_special_req_shipment_id
    on shipment_special_requirements (shipment_id);

-- Search runs by filename (re-processing detection)
create index idx_processed_emails_filename
    on processed_emails (filename);

-- Search shipments by route (common operational query)
create index idx_shipments_origin
    on shipments (origin_country, origin_city);

create index idx_shipments_dest
    on shipments (dest_country, dest_city);
