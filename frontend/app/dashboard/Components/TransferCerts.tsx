"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import React from "react";
import TransferCertificateCandidates from "./TransferCertificateCandidates";
import EditableCell from "./EditableCell";
import DocumentPreviewRow from "./DocumentPreviewRow";
const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

type TCRow = {
  doc_id: number;       // ✅ important
  file_id: number;
  student_name: string;
  father_name: string | null;
  mother_name: string | null;
  date_of_birth: string | null;
  lookup_status: string | null;
  last_class_studied: string | null;
  last_school_name: string | null;
};


export default function TransferCerts() {
  const [rows, setRows] = useState<TCRow[]>([]);
  const [expandedDocId, setExpandedDocId] = useState<number | null>(null);
  const [openPreviewDocId, setOpenPreviewDocId] = useState<number | null>(null);

  async function runPendingLookups() {
    const res = await apiFetch(
      `${API_BASE}/api/tc/lookup/pending`,
      { method: "POST" }
    );

    const data = await res.json();
    alert(`Processed ${data.processed_count} Transfer Certificate(s)`);

    const refreshed = await apiFetch(
      `${API_BASE}/api/transfer-certificates`
    );
    setRows(await refreshed.json());
  }
useEffect(() => {
  setOpenPreviewDocId(null);
}, [expandedDocId]);


  function fetchTransferCerts() {
    apiFetch(`${API_BASE}/api/transfer-certificates`)
      .then(res => res.json())
      .then(setRows)
      .catch(console.error);
  }
  useEffect(() => {
    apiFetch(`${API_BASE}/api/transfer-certificates`)
      .then(res => res.json())
      .then(setRows);
  }, []);
    async function rerunLookup(docId: number) {

    await apiFetch(
      `${API_BASE}/api/tc/${docId}/lookup?force=true`,
      { method: "POST" }
    );

    // refresh list
    const res = await apiFetch(`${API_BASE}/api/transfer-certificates`);
    setRows(await res.json());
  }

  return (
    <>
      <h3>Transfer Certificates</h3>

      <div style={{ overflowX: "auto" }}>
        <table className="table">
          <thead>
            <tr>
              <th>Student Name</th>
              <th>Father Name</th>
              <th>Mother Name</th>
              <th>DOB</th>
              <th>Lookup Status</th>
              <th>Last Class</th>
              <th>Last School</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <React.Fragment key={r.doc_id}>
                <tr key={`${r.doc_id}-row`}>
                  <td>
                    <EditableCell
                      value={r.student_name}
                      id={r.doc_id}
                      field="student_name"
                      endpoint="transfer-certificates"
                      onSaved={fetchTransferCerts}
                    />
                </td>
                  <td><EditableCell
                      value={r.father_name}
                      id={r.doc_id}
                      field="father_name"
                      endpoint="transfer-certificates"
                      onSaved={fetchTransferCerts}
                    />
                  </td>
                  <td><EditableCell
                      value={r.mother_name}
                      id={r.doc_id}
                      field="mother_name"
                      endpoint="transfer-certificates"
                      onSaved={fetchTransferCerts}
                    /></td>
                  <td><EditableCell
                      value={r.date_of_birth}
                      id={r.doc_id}
                      field="date_of_birth"
                      endpoint="transfer-certificates"
                      onSaved={fetchTransferCerts}
                    /></td>
                  <td>{r.lookup_status || "-"}</td>
                  <td><EditableCell
                      value={r.last_class_studied}
                      id={r.doc_id}
                      field="last_class_studied"
                      endpoint="transfer-certificates"
                      onSaved={fetchTransferCerts}
                    /></td>
                  <td><EditableCell
                      value={r.last_school_name}
                      id={r.doc_id}
                      field="last_school_name"
                      endpoint="transfer-certificates"
                      onSaved={fetchTransferCerts}
                    /></td>
                  <td>
                  <button
                    className="btn"
                    onClick={() =>
                      setExpandedDocId(
                        expandedDocId === r.doc_id ? null : r.doc_id
                      )
                    }
                  >
                    {expandedDocId === r.doc_id ? "Hide Matches" : "View Matches"}
                  </button>

                  <button
                    className="btn"
                    style={{ marginLeft: 6 }}
                    onClick={() =>
                      setOpenPreviewDocId(
                        openPreviewDocId === r.file_id ? null : r.file_id
                      )
                    }
                  >
                    {openPreviewDocId === r.file_id ? "Hide Preview" : "Preview"}
                  </button>

                  <button
                    className="btn"
                    style={{ marginLeft: 6 }}
                    onClick={() => rerunLookup(r.doc_id)}
                  >
                    🔄 Re-run
                  </button>
                </td>

                </tr>
                {openPreviewDocId === r.file_id && (
                <DocumentPreviewRow
                  key={`preview-${r.file_id}`}
                  fileId={r.file_id}
                  colSpan={8}
                  apiBase={API_BASE}
                />
              )}
                {expandedDocId === r.doc_id && (
                  <tr key={`${r.doc_id}-candidates`}>
                    <td colSpan={8} className="expanded-row">
                      <TransferCertificateCandidates docId={r.doc_id} />
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
        <button
          className="btn"
          onClick={runPendingLookups}
          style={{ marginBottom: 10 }}
        >
          Run Lookup for Pending Transfer Certificates
        </button>
      </div>
    </>
  );
}
