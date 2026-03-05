"use client";

import { useState, useEffect } from "react";
import { apiFetch } from "../../lib/api";
import React from "react";
import TransferCertificateCandidates from "./TransferCertificateCandidates";
import EditableCell from "./EditableCell";
import DocumentPreviewRow from "./DocumentPreviewRow";
import TransferCertificatesConfirmed from "./TransferCertificatesConfirmed";
import { useRowLock } from "../LockButton/useRowLock";
import LockButton from "../LockButton/LockButton";
import { usePaginatedApi } from "../Pagination/PaginatedApi";
import Pagination from "../Pagination/Pagination";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

type TCRow = {
  doc_id: number;
  file_id: number;
  student_name: string;
  father_name: string | null;
  mother_name: string | null;
  date_of_birth: string | null;
  lookup_status: string | null;
  last_class_studied: string | null;
  last_school_name: string | null;
};
type Props = {
  search: string;
};

export default function TransferCerts({ search }: Props) {
  const [expandedDocId, setExpandedDocId] = useState<number | null>(null);
  const [openPreviewDocId, setOpenPreviewDocId] = useState<number | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const { isRowEditable, setRow } = useRowLock<number>();

  const { items: rows, page, pageSize, total, setPage, refresh } = usePaginatedApi<TCRow>(
    `${API_BASE}/api/transfer-certificates`,
    search,
    50,
    [refreshKey],
  );

  const hasPending = rows.some(r => r.lookup_status === "pending");

  useEffect(() => {
    if (!hasPending) return;
    const id = setInterval(() => refresh(), 2000);
    return () => clearInterval(id);
  }, [hasPending, refresh]);

  async function runPendingLookups() {
    const res = await apiFetch(`${API_BASE}/api/tc/lookup/pending`, { method: "POST" });
    const data = await res.json();
    if (data.queued === 0) {
      alert("No pending Transfer Certificate lookups.");
    } else {
      setRefreshKey(k => k + 1);
    }
  }

  async function rerunLookup(docId: number) {
    await apiFetch(`${API_BASE}/api/tc/${docId}/lookup?force=true`, { method: "POST" });
    refresh();
  }

  return (
    <>
      <button
        className="btn"
        onClick={runPendingLookups}
        disabled={hasPending}
        style={{ marginBottom: 10 }}
      >
        {hasPending ? "⏳ Running Lookups…" : "Run Lookup for Pending Transfer Certificates"}
      </button>
      <div style={{ overflowX: "auto" }}>
        <table className="table">
          <thead>
            <tr>
              <th>File Id</th>
              <th>Student Name</th>
              <th>Father Name</th>
              <th>Mother Name</th>
              <th>DOB</th>
              <th>Lookup Status</th>
              <th>Last Class</th>
              <th>Last School</th>
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
                      <EditableCell value={r.student_name} id={r.doc_id} field="student_name" endpoint="transfer-certificates" onSaved={refresh} editable={editable} />
                    </td>
                    <td>
                      <EditableCell value={r.father_name} id={r.doc_id} field="father_name" endpoint="transfer-certificates" onSaved={refresh} editable={editable} />
                    </td>
                    <td>
                      <EditableCell value={r.mother_name} id={r.doc_id} field="mother_name" endpoint="transfer-certificates" onSaved={refresh} editable={editable} />
                    </td>
                    <td>
                      <EditableCell value={r.date_of_birth} id={r.doc_id} field="date_of_birth" endpoint="transfer-certificates" onSaved={refresh} editable={editable} />
                    </td>
                    <td>{r.lookup_status || "-"}</td>
                    <td>
                      <EditableCell value={r.last_class_studied} id={r.doc_id} field="last_class_studied" endpoint="transfer-certificates" onSaved={refresh} editable={editable} />
                    </td>
                    <td>
                      <EditableCell value={r.last_school_name} id={r.doc_id} field="last_school_name" endpoint="transfer-certificates" onSaved={refresh} editable={editable} />
                    </td>
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
                    <DocumentPreviewRow key={`preview-${r.file_id}`} fileId={r.file_id} colSpan={8} apiBase={API_BASE} />
                  )}
                  {expandedDocId === r.doc_id && (
                    <tr>
                      <td colSpan={8} className="expanded-row">
                        <TransferCertificatesConfirmed docId={r.doc_id} refreshKey={refreshKey} setRefreshKey={setRefreshKey} />
                        <TransferCertificateCandidates docId={r.doc_id} refreshKey={refreshKey} setRefreshKey={setRefreshKey} />
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
