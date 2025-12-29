"use client"

import SignalBadge from "./SignalBadge";
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import './dashboard.css';
const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;
type AadhaarConfirmedMatch = {
  match_id: number;
  sr: string;
  student_name: string;
  role: string;
  match_score: number;
  match_method: string;
  confirmed_on: string;
};

export default function AadhaarMatchesConfirmed({ docId,refreshKey,setRefreshKey }: { docId: number; refreshKey: number;setRefreshKey: React.Dispatch<React.SetStateAction<number>>; }){

const [rows, setRows] = useState<AadhaarConfirmedMatch[]>([]);
const [loading, setLoading] = useState(true);
useEffect(() => {
    const load = async () => {
      const res = await apiFetch(
        `${API_BASE}/api/aadhaar/${docId}/matches`
      );
      const data = await res.json();
      setRows(data);
    setLoading(false);
    };
    load();
  }, [docId,refreshKey]);
  if (!loading && rows.length === 0) {
    return null;
  }
return(
 <div>{!loading && <div className="confirmed-block">
    <table className="table confirmed-table">

          <thead>
            <tr>
              <th>SR</th>
              <th>Name</th>
              <th>Role</th>
              <th>Score</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <td> {r.sr}</td>
                <td>{r.student_name}</td>
                <td>{r.role}</td>
                <td>{r.match_score.toFixed(2)}</td>
                <td>
                <button
                  className="btn danger"
                  onClick={async () => {
                    if (!confirm(`Remove Aadhaar match for SR ${r.sr}?`)) return;

                    try {
                      await apiFetch(
                        `${API_BASE}/api/aadhaar/${r.sr}/${docId}/delete-match`,
                        { method: "DELETE" }
                      );     
                      setRefreshKey(k => k+1);          
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
    </div>}
</div>
)
}