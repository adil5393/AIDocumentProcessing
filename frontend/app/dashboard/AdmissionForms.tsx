import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";


export default function AdmissionForms() {
  /* ------------------ STATE ------------------ */
  const [rows, setRows] = useState<any[]>([]);
  const [reservedSRs, setReservedSRs] = useState<any[]>([]);
  const [srInput, setSrInput] = useState("");
  const [srMsg, setSrMsg] = useState("");

  /* ------------------ FETCHERS ------------------ */
  function fetchAdmissionForms() {
    apiFetch("http://localhost:8000/api/admission-forms")
      .then(res => res.json())
      .then(setRows)
      .catch(console.error);
  }

  function fetchReservedSRs() {
    apiFetch("http://localhost:8000/api/reserved")
      .then(res => res.json())
      .then(setReservedSRs)
      .catch(console.error);
  }

  /* ------------------ EFFECTS ------------------ */
  useEffect(() => {
    fetchAdmissionForms();
    fetchReservedSRs();

    const interval = setInterval(fetchReservedSRs, 5000);
    return () => clearInterval(interval);
  }, []);

  async function cleanupExpiredSRs() {
    const res = await apiFetch(
      "http://localhost:8000/api/cleanup",
      { method: "DELETE" }
    );

    const data = await res.json();

    alert(`Deleted ${data.deleted_count} expired SR(s)`);

    fetchReservedSRs(); // refresh left pane
  }
  /* ------------------ ACTIONS ------------------ */
  async function declareSR() {
    setSrMsg("");

    if (!srInput.trim()) {
      setSrMsg("Please enter SR");
      return;
    }

    const res = await apiFetch(
      "http://localhost:8000/api/declare",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
       body: JSON.stringify({  sr_number: srInput.trim().toUpperCase()})
      }
    );

    const data = await res.json();

    if (!res.ok) {
      if (typeof data.detail === "string") {
        setSrMsg(data.detail);
      } else if (Array.isArray(data.detail)) {
        setSrMsg(data.detail[0]?.msg || "Invalid input");
      } else {
        setSrMsg("Failed to reserve SR");
      }
      return;
    }

    setSrMsg(`SR ${srInput} reserved successfully`);
    setSrInput("");
    fetchReservedSRs();
  }

  /* ------------------ HELPERS ------------------ */
  function timeLeft(expiresAt: string) {
    const diff = new Date(expiresAt).getTime() - Date.now();
    if (diff <= 0) return "expired";

    const mins = Math.floor(diff / 60000);
    const secs = Math.floor((diff % 60000) / 1000);
    return `${mins}m ${secs}s`;
  }

  /* ------------------ RENDER ------------------ */
  return (
    <>
      <h3>Admission</h3>

      <div style={{ display: "flex", gap: 20 }}>

        {/* ================= LEFT PANE ================= */}
        <div style={{ width: "25%", borderRight: "1px solid #ccc", paddingRight: 10 }}>
          <h4>Reserved SRs</h4>

          {reservedSRs.length === 0 && (
            <p style={{ color: "#777" }}>No SRs reserved</p>
          )}

          <ul style={{ listStyle: "none", padding: 0 }}>
            {reservedSRs.map(sr => (
              <li
                key={sr.sr_number}
                style={{
                  marginBottom: 10,
                  padding: 6,
                  border: "1px solid #ddd",
                  borderRadius: 4
                }}
              >
                <strong>SR {sr.sr_number}</strong>
                <br />
                {/* <small>Branch: {sr.branch_id}</small>
                <br /> */}
                <small>Expires in: {timeLeft(sr.expires_at)}</small>
              </li>
            ))}
          </ul>
          <button
            onClick={cleanupExpiredSRs}
            style={{ marginTop: 10, width: "100%" }}
          >
            Cleanup Expired SRs
          </button>

          <hr />

          <h4>Declare / Reserve SR</h4>
          <input
            type="text"
            value={srInput}
            onChange={e => {
              const value = e.target.value.toUpperCase();
              if (/^[A-Z0-9\/\-]*$/.test(value)) {
                setSrInput(value);
              }
            }}
            placeholder="Enter SR"
            style={{ width: "100%", marginBottom: 6 }}
          />
          <button onClick={declareSR} style={{ width: "100%" }}>
            Reserve SR
          </button>

          {srMsg && <p style={{ marginTop: 8 }}>{srMsg}</p>}
        </div>

        {/* ================= RIGHT PANE ================= */}
        <div style={{ width: "75%" }}>
          <h4>Admission Forms</h4>

          <table className="table">
            <thead>
              <tr>
                <th>SR</th>
                <th>Class</th>
                <th>Name</th>
                <th>Gender</th>
                <th>DOB</th>
                <th>Father Name</th>
                <th>Mother Name</th>
                <th>Father Occupation</th>
                <th>Mother Occupation</th>
                <th>Address</th>
                <th>Phone 1</th>
                <th>Phone 2</th>
                <th>Aadhaar</th>
                <th>Last School</th>
                <th>Created At</th>
              </tr>
            </thead>

            <tbody>
              {rows.map(r => (
                <tr key={r.sr}>
                  <td>{r.sr}</td>
                  <td>{r.class}</td>
                  <td>{r.student_name}</td>
                  <td>{r.gender}</td>
                  <td>{r.date_of_birth}</td>
                  <td>{r.father_name}</td>
                  <td>{r.mother_name}</td>
                  <td>{r.father_occupation}</td>
                  <td>{r.mother_occupation}</td>
                  <td>{r.address}</td>
                  <td>{r.phone1}</td>
                  <td>{r.phone2}</td>
                  <td>{r.aadhaar_number}</td>
                  <td>{r.last_school_attended}</td>
                  <td>{r.created_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </div>
    </>
  );
}
