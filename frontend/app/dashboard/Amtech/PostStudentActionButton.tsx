"use client";

import { useState } from "react";
import { apiFetch } from "../../lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

type Props = {
  sr: string;
  endpoint: string; // e.g. "/api/students/process"
  onSuccess?: () => void;
};

export default function PostStudentActionButton({
  sr,
  endpoint,
  onSuccess,
}: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    setLoading(true);
    setError(null);

    try {
      const res = await apiFetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sr }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Failed");
      }

      onSuccess?.();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <button
        className="btn small"
        disabled={loading}
        onClick={handleClick}
      >
        {loading ? "Posting…" : "POST"}
      </button>

      {error && (
        <small style={{ color: "red" }}>
          {error}
        </small>
      )}
    </div>
  );
}
