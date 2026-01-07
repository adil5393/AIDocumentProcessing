"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useRouter } from "next/navigation";
import { matchesSearch } from "../Utils/Search";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

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
type Props = {
search: string;
}

export default function CrossReview({search}:Props) {
  const [students, setStudents] = useState<StudentOverview[]>([]);
  const [error, setError] = useState<string | null>(null);

  const router = useRouter();

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
        minHeight: 40,
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

  const loadStudents = async () => {
    try {
      const res = await apiFetch(
        `${API_BASE}/api/students/crossreview`
      );
      if (!res.ok) throw new Error("Failed to load students");
      setStudents(await res.json());
    } catch (e: any) {
      setError(e.message || "Failed to load students");
    }
  };

  useEffect(() => {
    loadStudents();
  }, []);

  const filteredRows = students.filter(r => matchesSearch(search, r.tc_name, r.admission_name, r.birth_certificate_name, r.aadhaar_name, r.sr ))

  return (
    <div style={{ padding: 12 }}>
      {error && <p style={{ color: "red" }}>{error}</p>}

      <table className="table">
        <thead>
          <tr>
            <th>SR</th>
            <th>Student</th>
            <th className="center">Aadhaar</th>
            <th className="center">TC</th>
            <th className="center">Marksheet</th>
            <th className="center">Birth Certificate</th>
            <th>Action</th>
          </tr>
        </thead>

        <tbody>
          {filteredRows.map(row => {
            const admission = row.admission_name.toLowerCase();

            return (
              <tr key={row.sr}>
                <td>{row.sr}</td>

                <td>
                  <strong>{row.admission_name}</strong>
                </td>

                <td style={{ textAlign: "center" }}>
                  <StatusCell
                    ok={row.aadhaar_confirmed}
                    mismatch={
                      !!row.aadhaar_name &&
                      admission !== row.aadhaar_name.toLowerCase()
                    }
                  />
                </td>

                <td style={{ textAlign: "center" }}>
                  <StatusCell
                    ok={row.tc_confirmed}
                    mismatch={
                      !!row.tc_name &&
                      admission !== row.tc_name.toLowerCase()
                    }
                  />
                </td>

                <td style={{ textAlign: "center" }}>
                  <StatusCell
                    ok={row.marksheet_confirmed}
                    mismatch={
                      !!row.marksheet_name &&
                      admission !== row.marksheet_name.toLowerCase()
                    }
                  />
                </td>

                <td style={{ textAlign: "center" }}>
                  <StatusCell
                    ok={row.birth_certificate_confirmed}
                    mismatch={
                      !!row.birth_certificate_name &&
                      admission !==
                        row.birth_certificate_name.toLowerCase()
                    }
                  />
                </td>

                <td>
                  <button
                    className="btn small"
                    onClick={() =>
                      router.push(`/students/${row.sr}`)
                    }
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
