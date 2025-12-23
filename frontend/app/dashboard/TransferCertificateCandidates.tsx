"use client";

import SignalBadge from "./SignalBadge";
import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

type TCCandidate = {
  sr: string;
  total_score: number;
  signals: Record<string, any>;
};

export default function TransferCertificateCandidates({ docId }: { docId: number }) {
  const [rows, setRows] = useState<TCCandidate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const res = await apiFetch(
        `http://localhost:8000/api/tc/${docId}/candidates`
      );
      const data = await res.json();
      setRows(data);
      setLoading(false);
    };
    load();
  }, [docId]);

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
            <td>{r.total_score.toFixed(2)}</td>
            <td>
              {Object.entries(r.signals).map(([k, v]) => (
                <SignalBadge key={k} label={k} value={v} />
              ))}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
