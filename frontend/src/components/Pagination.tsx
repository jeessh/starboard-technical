interface Props {
  page: number;
  totalPages: number;
  total: number;
  limit: number;
  onPage: (p: number) => void;
}

export default function Pagination({ page, totalPages, total, limit, onPage }: Props) {
  const from = Math.min((page - 1) * limit + 1, total);
  const to = Math.min(page * limit, total);

  return (
    <div className="pagination">
      <span className="pagination-info">
        {total === 0 ? "No records" : `${from}–${to} of ${total}`}
      </span>
      <div className="pagination-controls">
        <button
          className="btn btn-sm"
          disabled={page <= 1}
          onClick={() => onPage(1)}
        >
          «
        </button>
        <button
          className="btn btn-sm"
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
        >
          ‹
        </button>
        {Array.from({ length: totalPages }, (_, i) => i + 1)
          .filter((p) => p === 1 || p === totalPages || Math.abs(p - page) <= 1)
          .reduce<(number | "…")[]>((acc, p, i, arr) => {
            if (i > 0 && (p as number) - (arr[i - 1] as number) > 1) acc.push("…");
            acc.push(p);
            return acc;
          }, [])
          .map((p, i) =>
            p === "…" ? (
              <span key={`ellipsis-${i}`} className="pagination-ellipsis">…</span>
            ) : (
              <button
                key={p}
                className={`btn btn-sm ${p === page ? "btn-active" : ""}`}
                onClick={() => onPage(p as number)}
              >
                {p}
              </button>
            )
          )}
        <button
          className="btn btn-sm"
          disabled={page >= totalPages}
          onClick={() => onPage(page + 1)}
        >
          ›
        </button>
        <button
          className="btn btn-sm"
          disabled={page >= totalPages}
          onClick={() => onPage(totalPages)}
        >
          »
        </button>
      </div>
    </div>
  );
}
