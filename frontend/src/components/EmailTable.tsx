import type { ProcessedEmailSummary } from "../types";
import EmailRow from "./EmailRow";

interface Props {
  emails: ProcessedEmailSummary[];
  onDelete: (id: string) => void;
  onUpdate: (updated: ProcessedEmailSummary) => void;
}

export default function EmailTable({ emails, onDelete, onUpdate }: Props) {
  return (
    <div className="table-wrapper">
      <table className="email-table">
        <thead>
          <tr>
            <th style={{ width: 32 }} />
            <th>File</th>
            <th>Sender</th>
            <th>Company / Phone</th>
            <th className="td-center">Shipments</th>
            <th>Processed At</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {emails.length === 0 ? (
            <tr>
              <td colSpan={7} className="empty-state">
                No processed emails found. Submit one using the button above.
              </td>
            </tr>
          ) : (
            emails.map((e) => (
              <EmailRow
                key={e.id}
                summary={e}
                onDelete={onDelete}
                onUpdate={onUpdate}
              />
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
