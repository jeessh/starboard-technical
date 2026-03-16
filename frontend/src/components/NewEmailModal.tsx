import { useState } from "react";
import type { ProcessedEmail } from "../types";
import { processEmail } from "../api";

interface Props {
  onClose: () => void;
  onCreated: (email: ProcessedEmail) => void;
}

export default function NewEmailModal({ onClose, onCreated }: Props) {
  const [rawEmail, setRawEmail] = useState("");
  const [filename, setFilename] = useState("manual_entry");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!rawEmail.trim()) {
      setError("Email text cannot be empty.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await processEmail({ raw_email: rawEmail, filename });
      onCreated(result);
      onClose();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Process New Email</h2>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          <label className="form-label">Filename / Reference</label>
          <input
            className="input"
            value={filename}
            onChange={(e) => setFilename(e.target.value)}
            placeholder="e.g. 08_new_quote.txt"
          />

          <label className="form-label" style={{ marginTop: 16 }}>
            Raw Email Text
          </label>
          <textarea
            className="input"
            rows={14}
            value={rawEmail}
            onChange={(e) => setRawEmail(e.target.value)}
            placeholder={"Paste the full email here...\n\nSubject: ...\nFrom: ...\n\nBody..."}
          />

          {error && <p className="error-text">{error}</p>}
        </div>

        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose} disabled={loading}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={loading}>
            {loading ? "Extracting…" : "Extract & Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
