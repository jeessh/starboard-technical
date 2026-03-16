import { useState, useEffect, useCallback } from "react";
import type { ProcessedEmailSummary } from "./types";
import { getEmails } from "./api";
import EmailTable from "./components/EmailTable";
import Pagination from "./components/Pagination";
import NewEmailModal from "./components/NewEmailModal";
import "./App.css";

const PAGE_LIMIT = 5;

export default function App() {
  const [emails, setEmails] = useState<ProcessedEmailSummary[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);

  const fetchPage = useCallback(async (p: number) => {
    setLoading(true);
    setError(null);
    try {
      const result = await getEmails(p, PAGE_LIMIT);
      setEmails(result.data);
      setTotal(result.total);
      setTotalPages(result.total_pages);
      setPage(result.page);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPage(1);
  }, [fetchPage]);

  function handleDelete(id: string) {
    const remaining = emails.filter((e) => e.id !== id);
    if (remaining.length === 0 && page > 1) {
      fetchPage(page - 1);
    } else {
      fetchPage(page);
    }
  }

  function handleUpdate(updated: ProcessedEmailSummary) {
    setEmails((prev) =>
      prev.map((e) => (e.id === updated.id ? { ...e, ...updated } : e))
    );
  }

  function handleCreated() {
    fetchPage(1);
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-inner">
          <div>
            <h1 className="app-title">Freight RFQ Dashboard</h1>
            <p className="app-subtitle">Processed email extractions</p>
          </div>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            + New Email
          </button>
        </div>
      </header>

      <main className="app-main">
        {error && (
          <div className="alert alert-error">
            <strong>Error:</strong> {error}
            <button className="btn btn-sm btn-ghost" onClick={() => fetchPage(page)} style={{ marginLeft: 12 }}>
              Retry
            </button>
          </div>
        )}

        {loading ? (
          <div className="loading-state">Loading…</div>
        ) : (
          <EmailTable
            emails={emails}
            onDelete={handleDelete}
            onUpdate={handleUpdate}
          />
        )}

        <Pagination
          page={page}
          totalPages={totalPages}
          total={total}
          limit={PAGE_LIMIT}
          onPage={fetchPage}
        />
      </main>

      {showModal && (
        <NewEmailModal
          onClose={() => setShowModal(false)}
          onCreated={handleCreated}
        />
      )}
    </div>
  );
}
