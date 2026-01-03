import React, { useEffect, useState } from "react";
import EditableCell from "./EditableCell";
import DocumentPreviewRow from "./DocumentPreviewRow";
import BirthCertificateCandidates from "./BirthCertificateCandidates";
import BirthCertificateMatches from "./BirthCertificateMatches";
import { apiFetch } from "../../lib/api";

interface BirthCertificateRow {
  doc_id: number;
  file_id: number;
  student_name: string;
  father_name: string;
  mother_name: string;
  dob: string;
  lookup_status?: string;
}

export default function BirthCertificates({ API_BASE }: { API_BASE: string }) {
  const [rows, setRows] = useState<BirthCertificateRow[]>([]);
  const [expandedDocId, setExpandedDocId] = useState<number | null>(null);
  const [openPreviewDocId, setOpenPreviewDocId] = useState<number | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchBirthCertificates = async () => {
    const res = await apiFetch(`${API_BASE}/api/birth-certificates`);
    const data = await res.json();
    setRows(data);
  };

  const rerunLookup = async (docId: number) => {
    await apiFetch(`${API_BASE}/api/bc/${docId}/lookup`, {
      method: "POST",
    });
  };

  const runPendingLookups = async () => {
    await apiFetch(`${API_BASE}/api/bc/lookup/pending`, {
      method: "POST",
    });
    fetchBirthCertificates();
  };

  useEffect(() => {
    fetchBirthCertificates();
  }, [refreshKey]);

  return (
    <>
    <button
          className="btn"
          onClick={runPendingLookups}
          style={{ marginBottom: 10 }}
        >
          Run Lookup for Pending Birth Certificates
        </button>
      <div style={{ overflowX: "auto" }}>
        <table className="table">
          <thead>
            <tr>
              <th>Student Name</th>
              <th>Father Name</th>
              <th>Mother Name</th>
              <th>DOB</th>
              <th>Lookup Status</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            {rows.map((r) => (
              <React.Fragment key={r.doc_id}>
                <tr>
                  <td>
                    <EditableCell
                      value={r.student_name}
                      id={r.doc_id}
                      field="student_name"
                      endpoint="birth-certificates"
                      onSaved={fetchBirthCertificates}
                    />
                  </td>

                  <td>
                    <EditableCell
                      value={r.father_name}
                      id={r.doc_id}
                      field="father_name"
                      endpoint="birth-certificates"
                      onSaved={fetchBirthCertificates}
                    />
                  </td>

                  <td>
                    <EditableCell
                      value={r.mother_name}
                      id={r.doc_id}
                      field="mother_name"
                      endpoint="birth-certificates"
                      onSaved={fetchBirthCertificates}
                    />
                  </td>

                  <td>
                    <EditableCell
                      value={r.dob}
                      id={r.doc_id}
                      field="dob"
                      endpoint="birth-certificates"
                      onSaved={fetchBirthCertificates}
                    />
                  </td>

                  <td>{r.lookup_status || "-"}</td>

                  <td>
                    <button
                      className="btn"
                      onClick={() =>
                        setExpandedDocId(
                          expandedDocId === r.doc_id ? null : r.doc_id
                        )
                      }
                    >
                      {expandedDocId === r.doc_id
                        ? "Hide Matches"
                        : "View Matches"}
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
                      {openPreviewDocId === r.file_id
                        ? "Hide Preview"
                        : "Preview"}
                    </button>

                    <button
                      className="btn"
                      style={{ marginLeft: 6 }}
                      onClick={() => {
                        rerunLookup(r.doc_id);
                        setRefreshKey((k) => k + 1);
                      }}
                    >
                      🔄 Re-run
                    </button>
                  </td>
                </tr>

                {openPreviewDocId === r.file_id && (
                  <DocumentPreviewRow
                    key={`preview-${r.file_id}`}
                    fileId={r.file_id}
                    colSpan={6}
                    apiBase={API_BASE}
                  />
                )}

                {expandedDocId === r.doc_id && (
                  <tr>
                    <td colSpan={6} className="expanded-row">

                      {/* ✅ Confirmed FIRST */}
                      <BirthCertificateMatches
                        docId={r.doc_id}
                        refreshKey={refreshKey}
                        setRefreshKey={setRefreshKey}
                      />

                      {/* 🔽 Candidates BELOW */}
                      <BirthCertificateCandidates
                        docId={r.doc_id}
                        refreshKey={refreshKey}
                        setRefreshKey={setRefreshKey}
                      />

                    </td>
                  </tr>
)}
              </React.Fragment>
            ))}
          </tbody>
        </table>

        
      </div>
    </>
  );
}
