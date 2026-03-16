import { useState } from "react";
import type { ProcessedEmail, ProcessedEmailSummary, Shipment, ProcessedEmailUpdate } from "../types";
import { getEmail, updateEmail, deleteEmail } from "../api";
import ShipmentCard from "./ShipmentCard";

interface Props {
  summary: ProcessedEmailSummary;
  onDelete: (id: string) => void;
  onUpdate: (updated: ProcessedEmailSummary) => void;
}

export default function EmailRow({ summary, onDelete, onUpdate }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [detail, setDetail] = useState<ProcessedEmail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<ProcessedEmailUpdate>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function toggleExpand() {
    if (expanded) {
      setExpanded(false);
      return;
    }
    setExpanded(true);
    if (!detail) {
      setLoadingDetail(true);
      try {
        const d = await getEmail(summary.id);
        setDetail(d);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoadingDetail(false);
      }
    }
  }

  function startEdit(e: React.MouseEvent) {
    e.stopPropagation();
    setForm({
      filename: summary.filename,
      sender_name: summary.sender_name,
      sender_email: summary.sender_email,
      sender_company: summary.sender_company ?? undefined,
      sender_phone: summary.sender_phone ?? undefined,
    });
    setEditing(true);
    setError(null);
  }

  async function saveEdit(e: React.MouseEvent) {
    e.stopPropagation();
    setSaving(true);
    setError(null);
    try {
      const updated = await updateEmail(summary.id, form);
      onUpdate(updated);
      // Refresh detail if loaded
      if (detail) setDetail({ ...detail, ...updated });
      setEditing(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm(`Delete "${summary.filename}"?`)) return;
    try {
      await deleteEmail(summary.id);
      onDelete(summary.id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  function handleShipmentUpdate(updated: Shipment) {
    if (!detail) return;
    setDetail({
      ...detail,
      shipments: detail.shipments.map((s) => (s.id === updated.id ? updated : s)),
    });
  }

  function handleShipmentDelete(shipmentId: string) {
    if (!detail) return;
    const shipments = detail.shipments.filter((s) => s.id !== shipmentId);
    setDetail({ ...detail, shipments });
    onUpdate({ ...summary, shipment_count: shipments.length });
  }

  const date = new Date(summary.processed_at).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });

  return (
    <>
      <tr
        className={`email-row ${expanded ? "email-row-expanded" : ""}`}
        onClick={toggleExpand}
      >
        {/* Expand indicator */}
        <td className="td-expand">
          <span className="expand-icon">{expanded ? "▾" : "▸"}</span>
        </td>

        {/* File / sender */}
        <td>
          {editing ? (
            <input
              className="input-sm"
              value={form.filename ?? ""}
              onClick={(e) => e.stopPropagation()}
              onChange={(e) => setForm((f) => ({ ...f, filename: e.target.value }))}
            />
          ) : (
            <span className="filename">{summary.filename}</span>
          )}
        </td>

        <td>
          {editing ? (
            <div className="edit-stack" onClick={(e) => e.stopPropagation()}>
              <input className="input-sm" placeholder="Name" value={form.sender_name ?? ""} onChange={(e) => setForm((f) => ({ ...f, sender_name: e.target.value }))} />
              <input className="input-sm" placeholder="Email" value={form.sender_email ?? ""} onChange={(e) => setForm((f) => ({ ...f, sender_email: e.target.value }))} />
            </div>
          ) : (
            <div>
              <div className="sender-name">{summary.sender_name}</div>
              <div className="sender-email">{summary.sender_email}</div>
            </div>
          )}
        </td>

        <td>
          {editing ? (
            <div className="edit-stack" onClick={(e) => e.stopPropagation()}>
              <input className="input-sm" placeholder="Company" value={form.sender_company ?? ""} onChange={(e) => setForm((f) => ({ ...f, sender_company: e.target.value || null }))} />
              <input className="input-sm" placeholder="Phone" value={form.sender_phone ?? ""} onChange={(e) => setForm((f) => ({ ...f, sender_phone: e.target.value || null }))} />
            </div>
          ) : (
            <div>
              <div>{summary.sender_company ?? <span className="muted">—</span>}</div>
              <div className="muted">{summary.sender_phone}</div>
            </div>
          )}
        </td>

        <td className="td-center">
          <span className="shipment-badge">{summary.shipment_count}</span>
        </td>

        <td className="muted td-date">{date}</td>

        <td className="td-actions" onClick={(e) => e.stopPropagation()}>
          {!editing ? (
            <div className="row-actions">
              <button className="btn btn-sm btn-ghost" onClick={startEdit}>Edit</button>
              <button className="btn btn-sm btn-danger-ghost" onClick={handleDelete}>Delete</button>
            </div>
          ) : (
            <div className="row-actions">
              <button className="btn btn-sm btn-primary" onClick={saveEdit} disabled={saving}>{saving ? "…" : "Save"}</button>
              <button className="btn btn-sm btn-ghost" onClick={(e) => { e.stopPropagation(); setEditing(false); }}>Cancel</button>
            </div>
          )}
        </td>
      </tr>

      {expanded && (
        <tr className="expand-row">
          <td colSpan={7}>
            <div className="expand-content">
              {error && <p className="error-text">{error}</p>}
              {loadingDetail ? (
                <div className="loading-text">Loading shipments…</div>
              ) : detail ? (
                detail.shipments.length === 0 ? (
                  <p className="muted">No shipments extracted.</p>
                ) : (
                  <div className="shipments-grid">
                    {detail.shipments.map((s) => (
                      <ShipmentCard
                        key={s.id}
                        shipment={s}
                        onUpdate={handleShipmentUpdate}
                        onDelete={handleShipmentDelete}
                      />
                    ))}
                  </div>
                )
              ) : null}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
