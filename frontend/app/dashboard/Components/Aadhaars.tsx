"use client";

import AadhaarLookupCandidates from "./AadhaarCandidates";
import { useState, useEffect } from "react";
import { apiFetch } from "../../lib/api";
import React from "react";
import AadhaarMatchesConfirmed from "./AadhaarMatchesConfirmed";
import DocumentPreviewRow from "./DocumentPreviewRow";
import EditableCell from "./EditableCell";
import LockButton from "../LockButton/LockButton";
import { useRowLock } from "../LockButton/useRowLock";
import { usePaginatedApi } from "../Pagination/PaginatedApi";
import Pagination from "../Pagination/Pagination";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

type AadhaarRow = {
  doc_id: number;
  file_id:number;
  name: string;
  date_of_birth: string | null;
  aadhaar_number: string | null;
  relation_type: string | null;
  related_name: string | null;
  lookup_status: "pending" | "single_match" | "multiple_match" | "no_match" | "error" | "confirmed";
  lookup_checked_at: string | null;
  match_count: number;
};
type Props = {
  selectedDocId: number | null;
  onSelectDoc: (docId: number) => void;
  search: string;
};

export default function Aadhaars({ selectedDocId, onSelectDoc, search }: Props) {
  const [openPreviewDocId, setOpenPreviewDocId] = useState<number | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const {
    isRowEditable,
    setRow
  } = useRowLock<number>();

  const {
    items: rows,
    page,
    pageSize,
    total,
    setPage,
    refresh,
  } = usePaginatedApi<AadhaarRow>(
    `${API_BASE}/api/aadhaar-documents`,
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
    const res = await apiFetch(
      `${API_BASE}/api/aadhaar/lookup/pending`,
      { method: "POST" }
    );
    const data = await res.json();
    if (data.queued === 0) {
      alert("No pending Aadhaar lookups.");
    } else {
      setRefreshKey(k => k + 1);
    }
  }

  async function rerunLookup(docId: number) {
    await apiFetch(
      `${API_BASE}/api/aadhaar/${docId}/lookup?force=true`,
      { method: "POST" }
    );
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
        {hasPending ? "⏳ Running Lookups…" : "Run Lookup for Pending Aadhaar Documents"}
      </button>
      <div style={{ overflowX: "auto" }}>
        <table className="table">
          <thead>
            <tr>
              <th>File ID</th>
              <th>Name</th>
              <th>DOB</th>
              <th>Aadhaar</th>
              <th>Relation</th>
              <th>Related Name</th>
              <th>Matches</th>
              <th>Lookup Status</th>
              <th>Checked At</th>
              <th>Action</th>
              <th>Unlock To Edit</th>
            </tr>
          </thead>

         <tbody>
          {rows.map(r => {
          const editable = isRowEditable(r.doc_id);
          return (
          <React.Fragment key={r.doc_id}>
            <tr>
              <td>{r.file_id}</td>
              <td>
                  <EditableCell
                    value={r.name}
                    id={r.doc_id}
                    field="name"
                    endpoint="aadhaars"
                    onSaved={refresh}
                    editable={editable}
                  />
              </td>
              <td>
                  <EditableCell
                    value={r.date_of_birth || "-"}
                    id={r.doc_id}
                    field="date_of_birth"
                    endpoint="aadhaars"
                    onSaved={refresh}
                    editable={editable}
                  />
              </td>
              <td>
                  <EditableCell
                    value={r.aadhaar_number || "-"}
                    id={r.doc_id}
                    field="aadhaar_number"
                    endpoint="aadhaars"
                    onSaved={refresh}
                    editable={editable}
                  />
              </td>
              <td>{r.relation_type || "-"}</td>

              <td>
              <EditableCell
                    value={r.related_name || "-"}
                    id={r.doc_id}
                    field="related_name"
                    endpoint="aadhaars"
                    onSaved={refresh}
                    editable={editable}
                  />
              </td>
                <td>
                  {r.match_count}
                </td>

              <td>
                {r.lookup_status === "pending" && "⏳ Pending"}
                {r.lookup_status === "single_match" && "✅ Single Match"}
                {r.lookup_status === "multiple_match" && "⚠️ Multiple Matches"}
                {r.lookup_status === "no_match" && "❓ No Match"}
                {r.lookup_status === "error" && "❌ Error"}
                {r.lookup_status === "confirmed" && "Confirmed"}
              </td>

              <td>
                {r.lookup_checked_at
                  ? new Date(r.lookup_checked_at).toLocaleString()
                  : "-"}
              </td>

              <td>
                <button
                  className="btn"
                  onClick={() => onSelectDoc(r.doc_id)}
                  style={{ fontSize: 12 }}
                >
                  {selectedDocId === r.doc_id ? "Hide Matches" : "View Matches"}
                </button>

                <button
                  className="btn"
                  style={{ fontSize: 12, marginLeft: 6 }}
                  onClick={() =>
                    setOpenPreviewDocId(
                      openPreviewDocId === r.doc_id ? null : r.doc_id
                    )
                  }
                >
                  {openPreviewDocId === r.doc_id ? "Hide Preview" : "Preview"}
                </button>

                {r.lookup_status !== "pending" && (
                  <button
                    className="btn"
                    onClick={() => rerunLookup(r.doc_id)}
                    style={{ fontSize: 12, marginLeft: 6 }}
                  >
                    Re-run Lookup
                  </button>
                )}
              </td>
              <td><LockButton rowId={r.doc_id} unlocked={editable} onChange={state => setRow(r.doc_id, state)} /></td>
            </tr>
            {openPreviewDocId === r.doc_id && (
              <DocumentPreviewRow
                key={`preview-${r.file_id}`}
                fileId={r.file_id}
                colSpan={8}
                apiBase={API_BASE}
              />
            )}
            {selectedDocId === r.doc_id && (
              <tr>
                <td colSpan={10} className="expanded-row">
                  <div className="aadhaar-expanded">

                    {/* Confirmed matches FIRST */}
                    <AadhaarMatchesConfirmed docId={r.doc_id} refreshKey={refreshKey} setRefreshKey={setRefreshKey}/>

                    {/* Candidates BELOW */}
                    <AadhaarLookupCandidates docId={r.doc_id} refreshKey={refreshKey} setRefreshKey={setRefreshKey}/>

                  </div>
                </td>
              </tr>
            )}
          </React.Fragment>
        )})}
      </tbody>

        </table>
      </div>
      <Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
    </>
  );
}
