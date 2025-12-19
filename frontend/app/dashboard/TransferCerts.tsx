"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

type TCRow = {
  id?: number;
  student_name: string;
  father_name: string | null;
  mother_name: string | null;
  date_of_birth: string | null;
  last_class_studied: string | null;
  last_school_name: string | null;
};

export default function TransferCerts() {
  const [rows, setRows] = useState<TCRow[]>([]);

  useEffect(() => {
    apiFetch("http://localhost:8000/api/transfer-certificates")
      .then(res => res.json())
      .then(setRows);
  }, []);

  return (
    <>
      <h3>Transfer Certificates</h3>

      <div style={{ overflowX: "auto" }}>
        <table border={1} cellPadding={6} width="100%">
          <thead>
            <tr>
              <th>Student Name</th>
              <th>Father Name</th>
              <th>Mother Name</th>
              <th>DOB</th>
              <th>Last Class</th>
              <th>Last School</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, idx) => (
              <tr key={idx}>
                <td>{r.student_name}</td>
                <td>{r.father_name || "-"}</td>
                <td>{r.mother_name || "-"}</td>
                <td>{r.date_of_birth || "-"}</td>
                <td>{r.last_class_studied || "-"}</td>
                <td>{r.last_school_name || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
