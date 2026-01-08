"use client";

type PaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
};

export default function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
}: PaginationProps) {
  const totalPages = Math.ceil(total / pageSize);

  if (totalPages <= 1) return null;

  return (
    <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
      <button
        className="btn"
        disabled={page === 1}
        onClick={() => onPageChange(page - 1)}
      >
        ← Prev
      </button>

      <span>
        Page {page} of {totalPages}
      </span>

      <button
        className="btn"
        disabled={page === totalPages}
        onClick={() => onPageChange(page + 1)}
      >
        Next →
      </button>
    </div>
  );
}
