import type {
  PaginatedEmails,
  ProcessedEmail,
  ProcessedEmailUpdate,
  ProcessEmailRequest,
  Shipment,
  ShipmentUpdate,
} from "./types";

const BASE =
  import.meta.env.VITE_API_URL ??
  (import.meta.env.DEV
    ? "http://localhost:8000"
    : "https://starboard-technical.vercel.app");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${detail}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Emails ────────────────────────────────────────────────────────────────

export const getEmails = (page = 1, limit = 5) =>
  request<PaginatedEmails>(`/emails?page=${page}&limit=${limit}`);

export const getEmail = (id: string) =>
  request<ProcessedEmail>(`/emails/${id}`);

export const processEmail = (body: ProcessEmailRequest) =>
  request<ProcessedEmail>("/emails", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const updateEmail = (id: string, body: ProcessedEmailUpdate) =>
  request<ProcessedEmail>(`/emails/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });

export const deleteEmail = (id: string) =>
  request<void>(`/emails/${id}`, { method: "DELETE" });

// ── Shipments ─────────────────────────────────────────────────────────────

export const updateShipment = (id: string, body: ShipmentUpdate) =>
  request<Shipment>(`/shipments/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });

export const deleteShipment = (id: string) =>
  request<void>(`/shipments/${id}`, { method: "DELETE" });
