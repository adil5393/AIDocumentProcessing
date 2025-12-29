"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import "./dashboard.css";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

type TCConfirmedMatch = {
  match_id: number;
  sr: string;
  student_name: string | null;
  father_name: string | null;
  mother_name: string | null;
  date_of_birth: string | null;
  match_score: number;
  match_method: string;
  confirmed_on: string;
};
export default function TransferCertificatesConfirmed({
  docId,
  refreshKey,
  setRefreshKey,
}: {
  docId: number;
  refreshKey: number;
  setRefreshKey: React.Dispatch<React.SetStateAction<number>>;
}) {
  const [rows, setRows] = useState<TCConfirmedMatch[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await apiFetch(
          `${API_BASE}/api/transfer-certificates/${docId}/matches`
        );
        const data = await res.json();
        setRows(data);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [docId, refreshKey]);

  if (!loading && rows.length === 0) {
    return null;
  }

  return (
    <div>
      {!loading && (
        <div className="confirmed-block">
          <table className="table confirmed-table">
            <thead>
              <tr>
                <th>SR</th>
                <th>Name</th>
                <th>Score</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
                {rows.map(r => (
                    <tr key={r.match_id}>
                    <td>{r.sr}</td>
                    <td>
                        <strong>{r.student_name || "-"}</strong><br />
                        <small>
                        {r.father_name || "-"} / {r.mother_name || "-"}
                        </small><br />
                        <small>DOB: {r.date_of_birth || "-"}</small>
                    </td>
                    <td>{r.match_score}</td>
                    <td>
                        <button
                        className="btn danger"
                        onClick={async () => {
                            if (!confirm(`Remove TC match for SR ${r.sr}?`)) return;
                            await apiFetch(
                            `${API_BASE}/api/transfer-certificates/${r.sr}/${docId}/delete-match`,
                            { method: "DELETE" }
                            );
                            setRefreshKey(k => k + 1);
                        }}
                        >
                        Remove
                        </button>
                    </td>
                    </tr>
                ))}
                </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
