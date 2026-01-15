"use client";

import AadhaarLookupCandidates from "./AadhaarCandidates";
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import React from "react";
import AadhaarMatchesConfirmed from "./AadhaarMatchesConfirmed";
import DocumentPreviewRow from "./DocumentPreviewRow";
import { matchesSearch } from "../Utils/Search";
import EditableCell from "./EditableCell";
import LockButton from "../LockButton/LockButton";
import { useRowLock } from "../LockButton/useRowLock";

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
};
type Props = {
  selectedDocId: number | null;
  onSelectDoc: (docId: number) => void;
  search: string;
};

export default function Aadhaars({ selectedDocId, onSelectDoc, search }: Props) {
  const [rows, setRows] = useState<AadhaarRow[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);
  const [openPreviewDocId, setOpenPreviewDocId] = useState<number | null>(null);
  const {
      isRowEditable,
      setRow
    } = useRowLock<number>();

  function fetchAadhaarDocuments() {
    apiFetch(`${API_BASE}/api/aadhaar-documents`)
      .then(res => res.json())
      .then(setRows)
      .catch(console.error);
  }
  async function runPendingLookups() {
    const res = await apiFetch(
      `${API_BASE}/api/aadhaar/lookup/pending`,
      { method: "POST" }
    );

  const data = await res.json();
  alert(`Processed ${data.processed_count} Aadhaar document(s)`);

  fetchAadhaarDocuments();
}
  const filteredRows = rows.filter(r =>
  matchesSearch(
    search,
    r.name,
  )
);

  

  async function rerunLookup(docId: number) {
    await apiFetch(
      `${API_BASE}/api/aadhaar/${docId}/lookup?force=true`,
      { method: "POST" }
    );
    fetchAadhaarDocuments();
  }

  useEffect(() => {
    fetchAadhaarDocuments();
  }, [refreshKey]);

  return (
    <>
          <button className="btn"
            onClick={()=>{runPendingLookups(); setRefreshKey(k=>k+1);}}
            style={{ marginBottom: 10 }}
          >
            Run Lookup for Pending Aadhaar Documents
          </button>
      <div style={{ overflowX: "auto" }}>
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>DOB</th>
              <th>Aadhaar</th>
              <th>Relation</th>
              <th>Related Name</th>
              <th>Lookup Status</th>
              <th>Checked At</th>
              <th>Action</th>
              <th>Unlock To Edit</th>
              
            </tr>
          </thead>

         <tbody>
          {filteredRows.map(r => {
          const editable = isRowEditable(r.doc_id);
          return (
          <React.Fragment key={r.doc_id}>
            <tr>
              <td>
                  <EditableCell 
                    value={r.name}
                    id={r.doc_id}
                    field="name"
                    endpoint="aadhaars"
                    onSaved={()=>setRefreshKey(k => k+1)}
                    editable={editable}
                  />
              </td>
              <td>
                  <EditableCell 
                    value={r.date_of_birth || "-"}
                    id={r.doc_id}
                    field="date_of_birth"
                    endpoint="aadhaars"
                    onSaved={()=>setRefreshKey(k => k+1)}
                    editable={editable}
                  />
              </td>
              <td>
                  <EditableCell 
                    value={r.aadhaar_number || "-"}
                    id={r.doc_id}
                    field="aadhaar_number"
                    endpoint="aadhaars"
                    onSaved={()=>setRefreshKey(k => k+1)}
                    editable={editable}
                  />
              </td>
              <td>{r.relation_type || "-"}</td>
              <td>{r.related_name || "-"}</td>

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
                    onClick={() => {
                      rerunLookup(r.doc_id);
                      setRefreshKey(k => k + 1);
                    }}
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
                <td colSpan={8} className="expanded-row">
                  <div className="aadhaar-expanded">

                    {/* ✅ Confirmed matches FIRST */}
                    <AadhaarMatchesConfirmed docId={r.doc_id} refreshKey={refreshKey} setRefreshKey={setRefreshKey}/>

                    {/* 🔽 Candidates BELOW */}
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
    </>
  );
}
