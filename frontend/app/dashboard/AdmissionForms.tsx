import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

export default function AdmissionForms() {
  const [rows, setRows] = useState<any[]>([]);

  useEffect(() => {
    apiFetch("http://localhost:8000/api/admission-forms")
      .then(res => res.json())
      .then(setRows);
  }, []);

  return (
  <>
    <h3>Admission Forms</h3>

    <table border={1} cellPadding={6} width="100%">
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
  </>
);

}
