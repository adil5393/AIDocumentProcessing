"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

type AadhaarRow = {
  id?: number;
  name: string;
  date_of_birth: string | null;
  aadhaar_number: string | null;
  relation_type: string | null;
  related_name: string | null;
};

export default function Aadhaars() {
  const [rows, setRows] = useState<AadhaarRow[]>([]);

  useEffect(() => {
    apiFetch("http://localhost:8000/api/aadhaar-documents")
      .then(res => res.json())
      .then(setRows);
  }, []);

  return (
    <>
      <h3>Aadhaar Documents</h3>

      <div style={{ overflowX: "auto" }}>
        <table border={1} cellPadding={6} width="100%">
          <thead>
            <tr>
              <th>Name</th>
              <th>DOB</th>
              <th>Aadhaar</th>
              <th>Relation</th>
              <th>Related Name</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, idx) => (
              <tr key={idx}>
                <td>{r.name}</td>
                <td>{r.date_of_birth || "-"}</td>
                <td>{r.aadhaar_number || "-"}</td>
                <td>{r.relation_type || "-"}</td>
                <td>{r.related_name || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
