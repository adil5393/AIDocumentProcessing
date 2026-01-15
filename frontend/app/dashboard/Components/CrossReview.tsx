"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useRouter } from "next/navigation";
import { matchesSearch } from "../Utils/Search";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;
type Status = "ok" | "mismatch" | "pending" | "missing";
type PersonInfo = {
  student_name: string | null;
  father_name: string | null;
  mother_name: string | null;
  dob: string | null;
  confirmed: boolean | null;
};

type StudentRow = {
  sr: string;

  admission: PersonInfo;

  aadhaar: {
    student: PersonInfo;
    father: PersonInfo;
    mother: PersonInfo;
  };

  tc: PersonInfo;
  marksheet: PersonInfo;
  birth_certificate: PersonInfo;
};

function mapRow(r: any): StudentRow {
  return {
    sr: r.sr,

    admission: {
      student_name: r.admission_student_name,
      father_name: r.admission_father_name,
      mother_name: r.admission_mother_name,
      dob: r.admission_dob,
      confirmed: true,
    },

    aadhaar: {
      student: {
        student_name: r.aadhaar_student_name,
        father_name: null,
        mother_name: null,
        dob: r.aadhaar_dob,
        confirmed: r.aadhaar_student_confirmed,
      },
      father: {
        student_name: r.aadhaar_father_name,
        father_name: null,
        mother_name: null,
        dob: null,
        confirmed: r.aadhaar_father_confirmed,
      },
      mother: {
        student_name: r.aadhaar_mother_name,
        father_name: null,
        mother_name: null,
        dob: null,
        confirmed: r.aadhaar_mother_confirmed,
      },
    },

    tc: {
      student_name: r.tc_student_name,
      father_name: r.tc_father_name,
      mother_name: r.tc_mother_name,
      dob: r.tc_dob,
      confirmed: r.tc_confirmed,
    },

    marksheet: {
      student_name: r.marksheet_student_name,
      father_name: r.marksheet_father_name,
      mother_name: r.marksheet_mother_name,
      dob: r.marksheet_dob,
      confirmed: r.marksheet_confirmed,
    },

    birth_certificate: {
      student_name: r.bc_student_name,
      father_name: r.bc_father_name,
      mother_name: r.bc_mother_name,
      dob: r.bc_dob,
      confirmed: r.bc_confirmed,
    },
  };
}

function normalize(v: string | null) {
  return v?.toLowerCase().replace(/\s+/g, " ").trim() || null;
}

function computeStatus(
  admission: PersonInfo,
  doc: PersonInfo
): Status {
  if (!doc.student_name) return "missing";
  if (!doc.confirmed) return "pending";

  if (
    normalize(admission.student_name) !== normalize(doc.student_name) ||
    normalize(admission.father_name) !== normalize(doc.father_name) ||
    normalize(admission.mother_name) !== normalize(doc.mother_name) ||
    admission.dob !== doc.dob
  ) {
    return "mismatch";
  }

  return "ok";
}


const StatusCell = ({ status }: { status: Status }) => {
  const map: Record<Status, string> = {
    ok: "🟢",
    mismatch: "🔴",
    pending: "⏳",
    missing: "⚪",
  };

  return (
    <div style={{ fontSize: 18, textAlign: "center" }}>
      {map[status]}
    </div>
  );
};
function DetailsCell({
  status,
  doc,
}: {
  status: Status;
  doc: PersonInfo;
}) {
  const iconMap: Record<Status, string> = {
    ok: "🟢",
    mismatch: "🔴",
    pending: "⏳",
    missing: "⚪",
  };

  return (
    <div style={{ fontSize: 12, lineHeight: 1.4 }}>
      <div style={{ fontSize: 18, textAlign: "center" }}>
        {iconMap[status]}
      </div>

      {doc.student_name && (
        <div><strong>S:</strong> {doc.student_name}</div>
      )}
      {doc.father_name && (
        <div><strong>F:</strong> {doc.father_name}</div>
      )}
      {doc.mother_name && (
        <div><strong>M:</strong> {doc.mother_name}</div>
      )}
      {doc.dob && (
        <div><strong>DOB:</strong> {doc.dob}</div>
      )}
    </div>
  );
}



export default function CrossReview({ search }: { search: string }) {
  const [rows, setRows] = useState<StudentRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    (async () => {
      try {
        const res = await apiFetch(
          `${API_BASE}/api/students/crossreview`
        );
        if (!res.ok) throw new Error("Failed to load");
        const raw = await res.json();
        setRows(raw.map(mapRow));
      } catch (e: any) {
        setError(e.message);
      }
    })();
  }, []);

  const filtered = rows.filter(r =>
    matchesSearch(
      search,
      r.admission.student_name,
      r.sr
    )
  );
function computeParentStatus(
  admissionValue: string | null,
  doc: PersonInfo
): Status {
  if (!doc.student_name) return "missing";
  if (!doc.confirmed) return "pending";

  if (normalize(admissionValue) !== normalize(doc.student_name)) {
    return "mismatch";
  }

  return "ok";
}
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
            <th className="center">Birth Cert</th>
            <th>Action</th>
          </tr>
        </thead>

        <tbody>
          {filtered.map(r => (
            <tr key={r.sr}>
              <td>{r.sr}</td>
              <td><strong>{r.admission.student_name}</strong></td>

              <td>
                  {/* Student Aadhaar */}
                  <DetailsCell
                    status={computeStatus(
                      r.admission,
                      r.aadhaar.student
                    )}
                    doc={r.aadhaar.student}
                  />

                  <hr />

                  {/* Father Aadhaar */}
                  <DetailsCell
                    status={computeParentStatus(
                      r.admission.father_name,
                      r.aadhaar.father
                    )}
                    doc={r.aadhaar.father}
                  />

                  {/* Mother Aadhaar */}
                  <DetailsCell
                    status={computeParentStatus(
                      r.admission.mother_name,
                      r.aadhaar.mother
                    )}
                    doc={r.aadhaar.mother}
                  />
                </td>


              <td>
                <DetailsCell
                  status={computeStatus(r.admission, r.tc)}
                  doc={r.tc}
                />
              </td>

              <td>
                <DetailsCell
                  status={computeStatus(r.admission, r.marksheet)}
                  doc={r.marksheet}
                />
              </td>

              <td>
                <DetailsCell
                  status={computeStatus(
                    r.admission,
                    r.birth_certificate
                  )}
                  doc={r.birth_certificate}
                />
              </td>

              <td>
                <button
                  className="btn small"
                  onClick={() =>
                    router.push(`/students/${r.sr}`)
                  }
                >
                  View
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
