"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";
import React from "react";
import TransferCertificateCandidates from "./TransferCertificateCandidates";

type TCRow = {
  doc_id: number;          // ✅ important
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
  async function runPendingLookups() {
    const res = await apiFetch(
      "http://localhost:8000/api/tc/lookup/pending",
      { method: "POST" }
    );

    const data = await res.json();
    alert(`Processed ${data.processed_count} Transfer Certificate(s)`);

    const refreshed = await apiFetch(
      "http://localhost:8000/api/transfer-certificates"
    );
    setRows(await refreshed.json());
  }
  useEffect(() => {
    apiFetch("http://localhost:8000/api/transfer-certificates")
      .then(res => res.json())
      .then(setRows);
  }, []);
    async function rerunLookup(docId: number) {
    if (!confirm("Re-run lookup for this Transfer Certificate?")) return;

    await apiFetch(
      `http://localhost:8000/api/tc/${docId}/lookup?force=true`,
      { method: "POST" }
    );

    // refresh list
    const res = await apiFetch("http://localhost:8000/api/transfer-certificates");
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
                  <td>{r.student_name}</td>
                  <td>{r.father_name || "-"}</td>
                  <td>{r.mother_name || "-"}</td>
                  <td>{r.date_of_birth || "-"}</td>
                  <td>{r.lookup_status || "-"}</td>
                  <td>{r.last_class_studied || "-"}</td>
                  <td>{r.last_school_name || "-"}</td>
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
                      onClick={() => rerunLookup(r.doc_id)}
                    >
                      🔄 Re-run
                    </button>
                  </td>
                </tr>

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
