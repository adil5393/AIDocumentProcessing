"use client";

import SignalBadge from "./SignalBadge";
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import './dashboard.css';
const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

type AadhaarCandidate = {
  sr: string;
  role: string;
  student_name: string;
  total_score: number;
  signals: Record<string, any>;
};

export default function AadhaarLookupCandidates({ docId }: { docId: number }) {
  const [rows, setRows] = useState<AadhaarCandidate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const res = await apiFetch(
        `${API_BASE}/api/aadhaar/${docId}/candidates`
      );
      const data = await res.json();
      setRows(data);
      setLoading(false);
    };
    load();
  }, [docId]);

  if (loading) return <p>Loading Aadhaar matches…</p>;
  if (!rows.length) return <p>No Aadhaar matches found.</p>;

  return (
    <table className="table">
      <thead>
        <tr>
          <th>SR</th>
          <th>Role</th>
          <th>Name</th>
          <th>Score</th>
          <th>Signals</th>
          
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>
            <td> {r.sr}</td>
            <td>{r.role}</td>
            <td>{r.student_name}</td>
            <td>{r.total_score.toFixed(2)}</td>
            <td colSpan={8} className="expanded-row">
              {Object.entries(r.signals).map(([k, v]) => (
                <SignalBadge key={k} label={k} value={v} />
              ))}
            </td>
            <td><button
                className="btn"
                onClick={async () => {
                  if (!confirm("Confirm this Aadhaar match?")) return;

                  await apiFetch(
                    `${API_BASE}/api/aadhaar/${docId}/confirm`,
                    {
                      method: "POST",
                      body: JSON.stringify({
                        sr: r.sr,
                        role: r.role,
                        score: r.total_score,
                        method: "manual_confirm",
                      }),
                    }
                  );

                  alert("Match confirmed");
                }}
              >
                ✅ Confirm
              </button></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
