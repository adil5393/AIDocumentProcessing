"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import "./dashboard.css";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

type BirthCertificateConfirmedMatch = {
  match_id: number;
  sr: string;
  student_name: string;
  father_name?: string;
  mother_name?: string;
  date_of_birth?: string;
  match_score: number;
  match_method: string;
  confirmed_on: string;
};

export default function BirthCertificateMatches({
  docId,
  refreshKey,
  setRefreshKey,
}: {
  docId: number;
  refreshKey: number;
  setRefreshKey: React.Dispatch<React.SetStateAction<number>>;
}) {
  const [rows, setRows] = useState<BirthCertificateConfirmedMatch[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const res = await apiFetch(
        `${API_BASE}/api/birth-certificates/${docId}/matches`
      );
      const data = await res.json();
      setRows(data);
      setLoading(false);
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
              {rows.map((r, i) => (
                <tr key={i}>
                  <td>{r.sr}</td>
                  <td>{r.student_name}</td>
                  <td>{(r.match_score / 100).toFixed(2)}</td>
                  <td>
                    <button
                      className="btn danger"
                      onClick={async () => {
                        if (
                          !confirm(
                            `Remove Birth Certificate match for SR ${r.sr}?`
                          )
                        )
                          return;

                        try {
                          await apiFetch(
                            `${API_BASE}/api/birth-certificates/${r.sr}/${docId}/delete-match`,
                            { method: "DELETE" }
                          );
                          setRefreshKey((k) => k + 1);
                        } catch (err) {
                          alert("Failed to delete match");
                          console.error(err);
                        }
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
