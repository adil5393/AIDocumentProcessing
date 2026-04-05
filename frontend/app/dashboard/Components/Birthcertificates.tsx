import React, { useState, useEffect } from "react";
import EditableCell from "./EditableCell";
import DocumentPreviewRow from "./DocumentPreviewRow";
import BirthCertificateCandidates from "./BirthCertificateCandidates";
import BirthCertificateMatches from "./BirthCertificateMatches";
import { apiFetch } from "../../Lib/Api";
import LockButton from "../LockButton/LockButton";
import { useRowLock } from "../LockButton/useRowLock";
import { usePaginatedApi } from "../Pagination/PaginatedApi";
import Pagination from "../Pagination/Pagination";

interface BirthCertificateRow {
  doc_id: number;
  file_id: number;
  student_name: string;
  father_name: string;
  mother_name: string;
  date_of_birth: string;
  lookup_status?: string;
}
type Props = {
  API_BASE: string;
  search: string;
}

export default function BirthCertificates({ API_BASE, search }: Props) {
  const [expandedDocId, setExpandedDocId] = useState<number | null>(null);
  const [openPreviewDocId, setOpenPreviewDocId] = useState<number | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const { isRowEditable, setRow } = useRowLock<number>();

  const { items: rows, page, pageSize, total, setPage, refresh } = usePaginatedApi<BirthCertificateRow>(
    `${API_BASE}/api/birth-certificates`,
    search,
    50,
    [refreshKey],
  );

  const rerunLookup = async (docId: number) => {
    await apiFetch(`${API_BASE}/api/bc/${docId}/lookup`, { method: "POST" });
    refresh();
  };

  const hasPending = rows.some(r => r.lookup_status === "pending");

  useEffect(() => {
    if (!hasPending) return;
    const id = setInterval(() => refresh(), 2000);
    return () => clearInterval(id);
  }, [hasPending, refresh]);

  const runPendingLookups = async () => {
    const res = await apiFetch(`${API_BASE}/api/bc/lookup/pending`, { method: "POST" });
    const data = await res.json();
    if (data.queued === 0) {
      alert("No pending Birth Certificate lookups.");
    } else {
      setRefreshKey(k => k + 1);
    }
  };

  return (
    <>
      <button
        className="btn"
        onClick={runPendingLookups}
        disabled={hasPending}
        style={{ marginBottom: 10 }}
      >
        {hasPending ? "⏳ Running Lookups…" : "Run Lookup for Pending Birth Certificates"}
      </button>
      <div style={{ overflowX: "auto" }}>
        <table className="table">
          <thead>
            <tr>
              <th>File ID</th>
              <th>Student Name</th>
              <th>Father Name</th>
              <th>Mother Name</th>
              <th>DOB</th>
              <th>Lookup Status</th>
              <th>Actions</th>
              <th>Unlock To Edit</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const editable = isRowEditable(r.doc_id);
              return (
                <React.Fragment key={r.doc_id}>
                  <tr>
                    <td>{r.file_id}</td>
                    <td>
                      <EditableCell value={r.student_name} id={r.doc_id} field="student_name" endpoint="birth-certificates" onSaved={refresh} editable={editable} />
                    </td>
                    <td>
                      <EditableCell value={r.father_name} id={r.doc_id} field="father_name" endpoint="birth-certificates" onSaved={refresh} editable={editable} />
                    </td>
                    <td>
                      <EditableCell value={r.mother_name} id={r.doc_id} field="mother_name" endpoint="birth-certificates" onSaved={refresh} editable={editable} />
                    </td>
                    <td>
                      <EditableCell value={r.date_of_birth} id={r.doc_id} field="date_of_birth" endpoint="birth-certificates" onSaved={refresh} editable={editable} />
                    </td>
                    <td>{r.lookup_status || "-"}</td>
                    <td>
                      <button className="btn" onClick={() => setExpandedDocId(expandedDocId === r.doc_id ? null : r.doc_id)}>
                        {expandedDocId === r.doc_id ? "Hide Matches" : "View Matches"}
                      </button>
                      <button className="btn" style={{ marginLeft: 6 }} onClick={() => setOpenPreviewDocId(openPreviewDocId === r.file_id ? null : r.file_id)}>
                        {openPreviewDocId === r.file_id ? "Hide Preview" : "Preview"}
                      </button>
                      <button className="btn" style={{ marginLeft: 6 }} onClick={() => rerunLookup(r.doc_id)}>
                        🔄 Re-run
                      </button>
                    </td>
                    <td>
                      <LockButton rowId={r.doc_id} unlocked={editable} onChange={state => setRow(r.doc_id, state)} />
                    </td>
                  </tr>
                  {openPreviewDocId === r.file_id && (
                    <DocumentPreviewRow key={`preview-${r.file_id}`} fileId={r.file_id} colSpan={6} apiBase={API_BASE} />
                  )}
                  {expandedDocId === r.doc_id && (
                    <tr>
                      <td colSpan={6} className="expanded-row">
                        <BirthCertificateMatches docId={r.doc_id} refreshKey={refreshKey} setRefreshKey={setRefreshKey} />
                        <BirthCertificateCandidates docId={r.doc_id} refreshKey={refreshKey} setRefreshKey={setRefreshKey} />
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
      <Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
    </>
  );
}
