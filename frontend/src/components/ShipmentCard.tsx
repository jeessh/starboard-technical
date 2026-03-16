import { useState } from "react";
import type { Shipment, ShipmentUpdate } from "../types";
import { updateShipment, deleteShipment } from "../api";

const TRANSPORT_LABELS: Record<string, string> = {
  ocean_fcl: "Ocean FCL",
  ocean_lcl: "Ocean LCL",
  air: "Air",
};

interface Props {
  shipment: Shipment;
  onUpdate: (s: Shipment) => void;
  onDelete: (id: string) => void;
}

export default function ShipmentCard({ shipment, onUpdate, onDelete }: Props) {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<ShipmentUpdate>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const s = shipment;

  function startEdit() {
    setForm({
      transport_mode: s.transport_mode ?? undefined,
      incoterm: s.incoterm ?? undefined,
      origin_city: s.origin_city,
      origin_country: s.origin_country,
      origin_address: s.origin_address ?? undefined,
      dest_city: s.dest_city,
      dest_country: s.dest_country,
      dest_address: s.dest_address ?? undefined,
      cargo_description: s.cargo_description ?? undefined,
      weight_kg: s.weight_kg ?? undefined,
      volume_cbm: s.volume_cbm ?? undefined,
      container_type: s.container_type ?? undefined,
      container_count: s.container_count ?? undefined,
      piece_count: s.piece_count ?? undefined,
      special_requirements: [...s.special_requirements],
    });
    setEditing(true);
    setError(null);
  }

  async function saveEdit() {
    setLoading(true);
    setError(null);
    try {
      const updated = await updateShipment(s.id, form);
      onUpdate(updated);
      setEditing(false);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    if (!confirm("Delete this shipment?")) return;
    setLoading(true);
    try {
      await deleteShipment(s.id);
      onDelete(s.id);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
      setLoading(false);
    }
  }

  function field(label: string, value: string | number | null | undefined) {
    return value != null && value !== "" ? (
      <div className="detail-field">
        <span className="detail-label">{label}</span>
        <span className="detail-value">{String(value)}</span>
      </div>
    ) : null;
  }

  function editField(
    label: string,
    key: keyof ShipmentUpdate,
    type: "text" | "number" = "text"
  ) {
    return (
      <div className="detail-field">
        <label className="detail-label">{label}</label>
        <input
          className="input-sm"
          type={type}
          value={(form[key] as string | number | undefined) ?? ""}
          onChange={(e) =>
            setForm((f) => ({
              ...f,
              [key]: type === "number" ? (e.target.value === "" ? undefined : Number(e.target.value)) : e.target.value || undefined,
            }))
          }
        />
      </div>
    );
  }

  return (
    <div className="shipment-card">
      <div className="shipment-card-header">
        <div className="shipment-route">
          <span className="route-city">{s.origin_city}, {s.origin_country}</span>
          <span className="route-arrow">→</span>
          <span className="route-city">{s.dest_city}, {s.dest_country}</span>
          {s.transport_mode && (
            <span className="badge">{TRANSPORT_LABELS[s.transport_mode] ?? s.transport_mode}</span>
          )}
        </div>
        <div className="shipment-card-actions">
          {!editing && (
            <>
              <button className="btn btn-sm btn-ghost" onClick={startEdit} disabled={loading}>Edit</button>
              <button className="btn btn-sm btn-danger-ghost" onClick={handleDelete} disabled={loading}>Delete</button>
            </>
          )}
          {editing && (
            <>
              <button className="btn btn-sm btn-primary" onClick={saveEdit} disabled={loading}>{loading ? "Saving…" : "Save"}</button>
              <button className="btn btn-sm btn-ghost" onClick={() => setEditing(false)} disabled={loading}>Cancel</button>
            </>
          )}
        </div>
      </div>

      {error && <p className="error-text">{error}</p>}

      {!editing ? (
        <div className="detail-grid">
          {field("Incoterm", s.incoterm)}
          {field("Origin Address", s.origin_address)}
          {field("Dest Address", s.dest_address)}
          {field("Cargo", s.cargo_description)}
          {field("Weight", s.weight_kg != null ? `${s.weight_kg} kg` : null)}
          {field("Volume", s.volume_cbm != null ? `${s.volume_cbm} CBM` : null)}
          {field("Container", s.container_type)}
          {field("Containers", s.container_count)}
          {field("Pieces", s.piece_count)}
          {s.special_requirements.length > 0 && (
            <div className="detail-field detail-field-full">
              <span className="detail-label">Special Requirements</span>
              <div className="tag-list">
                {s.special_requirements.map((r, i) => (
                  <span key={i} className="tag">{r}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="detail-grid">
          <div className="detail-field">
            <label className="detail-label">Mode</label>
            <select
              className="input-sm"
              value={form.transport_mode ?? ""}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  transport_mode: (e.target.value as Shipment["transport_mode"]) || undefined,
                }))
              }
            >
              <option value="">—</option>
              <option value="ocean_fcl">Ocean FCL</option>
              <option value="ocean_lcl">Ocean LCL</option>
              <option value="air">Air</option>
            </select>
          </div>
          {editField("Incoterm", "incoterm")}
          {editField("Origin City", "origin_city")}
          {editField("Origin Country", "origin_country")}
          {editField("Origin Address", "origin_address")}
          {editField("Dest City", "dest_city")}
          {editField("Dest Country", "dest_country")}
          {editField("Dest Address", "dest_address")}
          {editField("Cargo", "cargo_description")}
          {editField("Weight (kg)", "weight_kg", "number")}
          {editField("Volume (CBM)", "volume_cbm", "number")}
          {editField("Container Type", "container_type")}
          {editField("Container Count", "container_count", "number")}
          {editField("Piece Count", "piece_count", "number")}
          <div className="detail-field detail-field-full">
            <label className="detail-label">Special Requirements (one per line)</label>
            <textarea
              className="input-sm"
              rows={3}
              value={(form.special_requirements ?? []).join("\n")}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  special_requirements: e.target.value.split("\n").filter(Boolean),
                }))
              }
            />
          </div>
        </div>
      )}
    </div>
  );
}
