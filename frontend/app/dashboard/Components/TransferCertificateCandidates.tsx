"use client";

import SignalBadge from "./SignalBadge";
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import './EditableCell'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

type TCCandidate = {
  sr: string;
  student_name: string;
  total_score: number;
  signals: Record<string, any>;
};

export default function TransferCertificateCandidates({ docId, refreshKey, setRefreshKey }: { docId: number, refreshKey: number,setRefreshKey: React.Dispatch<React.SetStateAction<number>>; }) {
  const [rows, setRows] = useState<TCCandidate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const res = await apiFetch(
        `${API_BASE}/api/tc/${docId}/candidates`
      );
      const data = await res.json();
      setRows(data);
      setLoading(false);
    };
    load();
  }, [docId, refreshKey]);

  if (loading) return <p>Loading TC matches…</p>;
  if (!rows.length) return <p>No TC matches found.</p>;

  return (
    <table width="100%" border={1} cellPadding={6}>
      <thead>
        <tr>
          <th>SR</th>
          <th>Score</th>
          <th>Signals</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>
            <td>{r.sr}</td>
            <td>{r.student_name}</td>
            <td>{r.total_score.toFixed(2)}</td>
            <td>
              {Object.entries(r.signals).map(([k, v]) => (
                <SignalBadge key={k} label={k} value={v} />
              ))}
            </td>
            <td>
            <button
              className="btn"
              onClick={async () => {
                if (!confirm("Confirm this Transfer Certificate match?")) return;

                await apiFetch(
                  `${API_BASE}/api/tc/${docId}/confirm`,
                  {
                    method: "POST",
                    body: JSON.stringify({
                      sr: r.sr,
                      score: r.total_score,
                      method: "manual_confirm",
                    }),
                  }
                );
                setRefreshKey(k => k+1);
                alert("TC match confirmed");
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
