"use client";

import { useState } from "react";
import { apiFetch } from "../../lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

export default function AmtechPanel() {
  const [status, setStatus] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const reconnect = async () => {
    await apiFetch(`${API_BASE}/api/amtech/reconnect`, {
      method: "POST",
    });
    loadStatus();
  };

  return (
    <div style={{ padding: 12 }}>
      <h2>Amtech Integration</h2>

      <button className="btn" onClick={loadStatus}>
        Check Connection
      </button>

      {loading && <p>Checking connection…</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      {status && (
        <div style={{ marginTop: 10 }}>
          <p>
            Status:{" "}
            {status.connected ? "🟢 Connected" : "🔴 Disconnected"}
          </p>

          {status.connected && (
            <>
              <p>User ID: {status.user_id}</p>
              <p>
                Token expires in:{" "}
                {Math.floor(status.expires_in_seconds / 3600)} hours
              </p>

              <h4>Branches</h4>
              <ul>
                {status.branches?.map((b: any) => (
                  <li key={b.branch.master_id}>
                    {b.branch.branch_name}
                  </li>
                ))}
              </ul>
            </>
          )}

          <button className="btn" onClick={reconnect}>
            🔁 Reconnect Amtech
          </button>
        </div>
      )}
    </div>
  );
}
