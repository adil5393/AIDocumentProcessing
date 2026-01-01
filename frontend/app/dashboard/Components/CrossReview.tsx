"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useRouter } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

type AmtechBranch = {
  user_branch_id: number;
  branch: {
    branch_name: string;
    master_id: string;
  };
  school: {
    school_name: string;
    master_id: string;
  };
};

type StudentOverview = {
  sr: string;
  admission_name: string;

  aadhaar_name: string | null;
  aadhaar_confirmed: boolean | null;

  tc_name: string | null;
  tc_confirmed: boolean | null;

  marksheet_name: string | null;
  marksheet_confirmed: boolean | null;

  birth_certificate_name: string | null;
  birth_certificate_confirmed: boolean | null;
};

type AmtechStatus = {
  connected: boolean;
  user_id: string;
  branches: AmtechBranch[];
  expires_at: number;
  expires_in_seconds: number;
};

export default function CrossReview() {

  const [status, setStatus] = useState<AmtechStatus  | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedBranchId, setSelectedBranchId] = useState<string | null>(null);
  const [students, setStudents] = useState<StudentOverview[]>([]);
  const StatusCell = ({
  ok,
  mismatch,
}: {
  ok: boolean | null;
  mismatch: boolean;
}) => (
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      lineHeight: 1.2,
      minHeight: 40, // 👈 stabilizes row height
    }}
  >
    <span style={{ fontSize: 18 }}>
      {ok ? "🟢" : "🔴"}
    </span>

    {mismatch && (
      <span
        style={{
          color: "#b45309",
          fontSize: 11,
          marginTop: 2,
          whiteSpace: "nowrap",
        }}
      >
        ⚠ Name mismatch
      </span>
    )}
  </div>
);
  const router = useRouter();

  const isConnected = status?.connected ?? false;
  const branches = status?.branches ?? [];
  const hoursLeft = status
  ? Math.floor(status.expires_in_seconds / 3600)
  : null;
  const loadStudents = async () => {
  try {
    const res = await apiFetch(`${API_BASE}/api/amtech/overview`);
    if (!res.ok) throw new Error("Failed to load students");
    setStudents(await res.json());
  } catch (e: any) {
    setError(e.message || "Failed to load students");
  }
};
  const loadStatus = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await apiFetch(`${API_BASE}/api/amtech/status`);
      if (!res.ok) throw new Error("Failed to fetch Amtech status");
      setStatus(await res.json());
    } catch (e: any) {
      setError(e.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };
useEffect(() => {
  loadStudents();
}, []); 
  useEffect(() => {
    if (branches.length > 0 && !selectedBranchId) {
      setSelectedBranchId(branches[0].branch.master_id);
    }
  }, [branches, selectedBranchId]);
  useEffect(() => {
  loadStatus();
  }, []);
  const reconnect = async () => {
    await apiFetch(`${API_BASE}/api/amtech/reconnect`, {
      method: "POST",
    });
    loadStatus();
  };

  return (
  <div style={{ padding: 12 }}>
    <h2>Amtech Integration</h2>

    <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
      <button
        className="btn"
        onClick={loadStatus}
        disabled={loading}
      >
        🔍 Check Connection
      </button>

      {!isConnected && status && (
        <button
          className="btn danger"
          onClick={reconnect}
          disabled={loading}
        >
          🔁 Reconnect
        </button>
      )}
    </div>

    {loading && <p>Checking connection…</p>}
    {error && <p style={{ color: "red" }}>{error}</p>}
  
    { status && (
      <div style={{ marginTop: 10 }}>
        <p>
          Status:{" "}
          {isConnected ? "🟢 Connected" : "🔴 Disconnected"}
        </p>

        <p>User ID: {status.user_id}</p>

        {isConnected && hoursLeft !== null && (
          <p>Token expires in: {hoursLeft} hours</p>
        )}

        {branches.length > 0 && (
  <>
    <h4>Select Branch</h4>

    <select
      value={selectedBranchId ?? ""}
      onChange={(e) => setSelectedBranchId(e.target.value)}
      style={{ padding: 6, minWidth: 250 }}
    >
      {branches.map(b => (
        <option
          key={b.branch.master_id}
          value={b.branch.master_id}
        >
          {b.branch.branch_name}
        </option>
      ))}
    </select>
    
  </>
)}
      </div>
    )}
  <table className="table">
  <thead>
    <tr>
      <th>SR</th>
      <th>Student</th>
      <th>Aadhaar</th>
      <th>TC</th>
      <th>Marksheet</th>
      <th>Birth Certificate</th>
      <th>Action</th>
    </tr>
  </thead>

  <tbody>
  {students.map(row => {
    const admission = row.admission_name.toLowerCase();

    return (
      <tr key={row.sr}>
        <td>{row.sr}</td>

        {/* Admission */}
        <td>
          <strong>{row.admission_name}</strong>
        </td>

        {/* Aadhaar */}
        <td style={{ verticalAlign: "middle" }}>
          <StatusCell
            ok={row.aadhaar_confirmed}
            mismatch={
              !!row.aadhaar_name &&
              admission !== row.aadhaar_name.toLowerCase()
            }
          />
        </td>

        {/* TC */}
        <td style={{ verticalAlign: "middle" }}>
          <StatusCell
            ok={row.tc_confirmed}
            mismatch={
              !!row.tc_name &&
              admission !== row.tc_name.toLowerCase()
            }
          />
        </td>

        {/* Marksheet */}
        <td style={{ verticalAlign: "middle" }}>
          <StatusCell
            ok={row.marksheet_confirmed}
            mismatch={
              !!row.marksheet_name &&
              admission !== row.marksheet_name.toLowerCase()
            }
          />
        </td>

        {/* Birth Certificate */}
        <td style={{ verticalAlign: "middle" }}>
          <StatusCell
            ok={row.birth_certificate_confirmed}
            mismatch={
              !!row.birth_certificate_name &&
              admission !== row.birth_certificate_name.toLowerCase()
            }
          />
        </td>

        {/* Action */}
        <td>
          <button
            className="btn small"
            onClick={() => router.push(`/students/${row.sr}`)}
          >
            View
          </button>
        </td>
      </tr>
    );
  })}
</tbody>

</table>

  </div>
  
);

}
