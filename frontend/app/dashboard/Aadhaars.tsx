"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

type AadhaarRow = {
  doc_id: number;
  name: string;
  date_of_birth: string | null;
  aadhaar_number: string | null;
  relation_type: string | null;
  related_name: string | null;
  lookup_status: "pending" | "single_match" | "multiple_match" | "no_match" | "error";
  lookup_checked_at: string | null;
};


export default function Aadhaars() {
  const [rows, setRows] = useState<AadhaarRow[]>([]);

  function fetchAadhaarDocuments() {
    apiFetch("http://localhost:8000/api/aadhaar-documents")
      .then(res => res.json())
      .then(setRows)
      .catch(console.error);
  }
async function runPendingLookups() {
  const res = await apiFetch(
    "http://localhost:8000/api/aadhaar/lookup/pending",
    { method: "POST" }
  );

  const data = await res.json();
  alert(`Processed ${data.processed_count} Aadhaar document(s)`);

  fetchAadhaarDocuments();
}

  async function rerunLookup(docId: number) {
    await apiFetch(
      `http://localhost:8000/api/aadhaar/${docId}/lookup?force=true`,
      { method: "POST" }
    );
    fetchAadhaarDocuments();
  }

  useEffect(() => {
    fetchAadhaarDocuments();
  }, []);

  return (
    <>
      <h3>Aadhaar Documents</h3>

      <div style={{ overflowX: "auto" }}>
        <table border={1} cellPadding={6} width="100%">
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
            </tr>
          </thead>

          <tbody>
            {rows.map(r => (
              <tr key={r.doc_id}>
                <td>{r.name}</td>
                <td>{r.date_of_birth || "-"}</td>
                <td>{r.aadhaar_number || "-"}</td>
                <td>{r.relation_type || "-"}</td>
                <td>{r.related_name || "-"}</td>

                <td>
                  {r.lookup_status === "pending" && "⏳ Pending"}
                  {r.lookup_status === "single_match" && "✅ Single Match"}
                  {r.lookup_status === "multiple_match" && "⚠️ Multiple Matches"}
                  {r.lookup_status === "no_match" && "❓ No Match"}
                  {r.lookup_status === "error" && "❌ Error"}
                </td>

                <td>
                  {r.lookup_checked_at
                    ? new Date(r.lookup_checked_at).toLocaleString()
                    : "-"}
                </td>

                <td>
                  {r.lookup_status !== "pending" && (
                    <button
                      onClick={() => rerunLookup(r.doc_id)}
                      style={{ fontSize: 12 }}
                    >
                      Re-run Lookup
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
          <button
            onClick={runPendingLookups}
            style={{ marginBottom: 10 }}
          >
            Run Lookup for Pending Aadhaar Documents
          </button>
      </div>
    </>
  );
}
