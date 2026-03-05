"use client";

import React, { useState } from "react";
import { usePaginatedApi } from "../Pagination/PaginatedApi";
import Pagination from "../Pagination/Pagination";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

type DocStatus = "ok" | "mismatch" | "pending" | "missing";

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
  aadhaar: { student: PersonInfo; father: PersonInfo; mother: PersonInfo };
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

function normalize(v: string | null | undefined) {
  return v?.toLowerCase().replace(/\s+/g, " ").trim() ?? null;
}

// Compare a full document (name + father + mother + dob) against admission
function analyzeDoc(
  admission: PersonInfo,
  doc: PersonInfo
): { status: DocStatus; issues: string[] } {
  if (!doc.student_name) return { status: "missing", issues: [] };
  if (!doc.confirmed) return { status: "pending", issues: [] };

  const issues: string[] = [];
  if (normalize(admission.student_name) !== normalize(doc.student_name))
    issues.push("name");
  if (doc.father_name !== null && normalize(admission.father_name) !== normalize(doc.father_name))
    issues.push("father");
  if (doc.mother_name !== null && normalize(admission.mother_name) !== normalize(doc.mother_name))
    issues.push("mother");
  if (doc.dob !== null && admission.dob !== doc.dob)
    issues.push("dob");

  return { status: issues.length > 0 ? "mismatch" : "ok", issues };
}

// Compare a parent aadhaar (name only) against admission
function analyzeParentAadhaar(
  admissionName: string | null,
  doc: PersonInfo
): { status: DocStatus; issues: string[] } {
  if (!doc.student_name) return { status: "missing", issues: [] };
  if (!doc.confirmed) return { status: "pending", issues: [] };

  const issues: string[] = [];
  if (normalize(admissionName) !== normalize(doc.student_name)) issues.push("name");

  return { status: issues.length > 0 ? "mismatch" : "ok", issues };
}

// ── Badge ──────────────────────────────────────────────────────────────────

const BADGE_STYLE: Record<DocStatus, React.CSSProperties> = {
  ok:       { background: "#d1fae5", color: "#065f46", borderColor: "#6ee7b7" },
  mismatch: { background: "#fee2e2", color: "#991b1b", borderColor: "#fca5a5" },
  pending:  { background: "#fef3c7", color: "#92400e", borderColor: "#fcd34d" },
  missing:  { background: "#f3f4f6", color: "#9ca3af", borderColor: "#d1d5db" },
};
const BADGE_ICON: Record<DocStatus, string> = {
  ok: "✓", mismatch: "✗", pending: "⏳", missing: "—",
};

function DocBadge({
  label,
  status,
  issues,
}: {
  label: string;
  status: DocStatus;
  issues: string[];
}) {
  const s = BADGE_STYLE[status];
  const tooltip =
    issues.length > 0 ? `Mismatched: ${issues.join(", ")}` : status;
  return (
    <span
      title={tooltip}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 3,
        padding: "2px 7px",
        borderRadius: 4,
        fontSize: 11,
        fontWeight: 600,
        border: `1px solid ${s.borderColor}`,
        background: s.background,
        color: s.color,
        margin: "1px 2px",
        cursor: "default",
        whiteSpace: "nowrap",
      }}
    >
      {label} {BADGE_ICON[status]}
    </span>
  );
}

// ── Comparison table (expanded row) ───────────────────────────────────────

function CmpCell({
  base,
  val,
  confirmed,
}: {
  base: string | null;
  val: string | null;
  confirmed: boolean | null;
}) {
  if (val === null)
    return (
      <td style={{ color: "#9ca3af", textAlign: "center", fontSize: 12 }}>—</td>
    );

  const pending = confirmed === false;
  const match = normalize(base) === normalize(val);
  const bg = pending ? "#fefce8" : match ? "#f0fdf4" : "#fef2f2";
  const color = pending ? "#92400e" : match ? "#166534" : "#991b1b";

  return (
    <td style={{ background: bg, color, fontSize: 12, padding: "4px 8px" }}>
      {val}
      <span style={{ fontSize: 10, marginLeft: 3 }}>
        {pending ? "(pending)" : match ? "✓" : "✗"}
      </span>
    </td>
  );
}

function CompareTable({ r }: { r: StudentRow }) {
  const th: React.CSSProperties = {
    fontSize: 11,
    fontWeight: 700,
    padding: "4px 8px",
    background: "#f3f4f6",
    borderBottom: "1px solid #e5e7eb",
    whiteSpace: "nowrap",
  };
  const tdLabel: React.CSSProperties = {
    fontSize: 12,
    fontWeight: 600,
    padding: "4px 8px",
    whiteSpace: "nowrap",
    color: "#374151",
  };
  const tdBase: React.CSSProperties = {
    fontSize: 12,
    padding: "4px 8px",
    fontWeight: 600,
    color: "#1e3a5f",
    background: "#eff6ff",
  };

  return (
    <table
      style={{
        width: "100%",
        borderCollapse: "collapse",
        border: "1px solid #e5e7eb",
        borderRadius: 6,
        overflow: "hidden",
      }}
    >
      <thead>
        <tr>
          <th style={th}>Field</th>
          <th style={{ ...th, background: "#dbeafe" }}>Admission (base)</th>
          <th style={th}>Aadhaar S</th>
          <th style={th}>Aadhaar F</th>
          <th style={th}>Aadhaar M</th>
          <th style={th}>TC</th>
          <th style={th}>Marksheet</th>
          <th style={th}>Birth Cert</th>
        </tr>
      </thead>
      <tbody>
        {/* Student Name */}
        <tr>
          <td style={tdLabel}>Student Name</td>
          <td style={tdBase}>{r.admission.student_name ?? "—"}</td>
          <CmpCell base={r.admission.student_name} val={r.aadhaar.student.student_name} confirmed={r.aadhaar.student.confirmed} />
          <td style={{ color: "#9ca3af", textAlign: "center", fontSize: 12 }}>—</td>
          <td style={{ color: "#9ca3af", textAlign: "center", fontSize: 12 }}>—</td>
          <CmpCell base={r.admission.student_name} val={r.tc.student_name} confirmed={r.tc.confirmed} />
          <CmpCell base={r.admission.student_name} val={r.marksheet.student_name} confirmed={r.marksheet.confirmed} />
          <CmpCell base={r.admission.student_name} val={r.birth_certificate.student_name} confirmed={r.birth_certificate.confirmed} />
        </tr>
        {/* Father Name */}
        <tr>
          <td style={tdLabel}>Father Name</td>
          <td style={tdBase}>{r.admission.father_name ?? "—"}</td>
          <td style={{ color: "#9ca3af", textAlign: "center", fontSize: 12 }}>—</td>
          <CmpCell base={r.admission.father_name} val={r.aadhaar.father.student_name} confirmed={r.aadhaar.father.confirmed} />
          <td style={{ color: "#9ca3af", textAlign: "center", fontSize: 12 }}>—</td>
          <CmpCell base={r.admission.father_name} val={r.tc.father_name} confirmed={r.tc.confirmed} />
          <CmpCell base={r.admission.father_name} val={r.marksheet.father_name} confirmed={r.marksheet.confirmed} />
          <CmpCell base={r.admission.father_name} val={r.birth_certificate.father_name} confirmed={r.birth_certificate.confirmed} />
        </tr>
        {/* Mother Name */}
        <tr>
          <td style={tdLabel}>Mother Name</td>
          <td style={tdBase}>{r.admission.mother_name ?? "—"}</td>
          <td style={{ color: "#9ca3af", textAlign: "center", fontSize: 12 }}>—</td>
          <td style={{ color: "#9ca3af", textAlign: "center", fontSize: 12 }}>—</td>
          <CmpCell base={r.admission.mother_name} val={r.aadhaar.mother.student_name} confirmed={r.aadhaar.mother.confirmed} />
          <CmpCell base={r.admission.mother_name} val={r.tc.mother_name} confirmed={r.tc.confirmed} />
          <CmpCell base={r.admission.mother_name} val={r.marksheet.mother_name} confirmed={r.marksheet.confirmed} />
          <CmpCell base={r.admission.mother_name} val={r.birth_certificate.mother_name} confirmed={r.birth_certificate.confirmed} />
        </tr>
        {/* Date of Birth */}
        <tr>
          <td style={tdLabel}>Date of Birth</td>
          <td style={tdBase}>{r.admission.dob ?? "—"}</td>
          <CmpCell base={r.admission.dob} val={r.aadhaar.student.dob} confirmed={r.aadhaar.student.confirmed} />
          <td style={{ color: "#9ca3af", textAlign: "center", fontSize: 12 }}>—</td>
          <td style={{ color: "#9ca3af", textAlign: "center", fontSize: 12 }}>—</td>
          <CmpCell base={r.admission.dob} val={r.tc.dob} confirmed={r.tc.confirmed} />
          <CmpCell base={r.admission.dob} val={r.marksheet.dob} confirmed={r.marksheet.confirmed} />
          <CmpCell base={r.admission.dob} val={r.birth_certificate.dob} confirmed={r.birth_certificate.confirmed} />
        </tr>
      </tbody>
    </table>
  );
}

// ── Legend ─────────────────────────────────────────────────────────────────

function Legend() {
  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
      <DocBadge label="Matched" status="ok" issues={[]} />
      <DocBadge label="Mismatch" status="mismatch" issues={[]} />
      <DocBadge label="Pending" status="pending" issues={[]} />
      <DocBadge label="Missing" status="missing" issues={[]} />
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────

export default function CrossReview({ search }: { search: string }) {
  const [expandedSr, setExpandedSr] = useState<string | null>(null);
  const [showIssuesOnly, setShowIssuesOnly] = useState(false);

  const { items, page, total, pageSize, setPage } =
    usePaginatedApi<any>(`${API_BASE}/api/students/crossreview`, search, 50, []);

  const rows = items.map(mapRow);

  const filtered = showIssuesOnly
    ? rows.filter((r) => {
        const checks = [
          analyzeDoc(r.admission, r.aadhaar.student),
          analyzeParentAadhaar(r.admission.father_name, r.aadhaar.father),
          analyzeParentAadhaar(r.admission.mother_name, r.aadhaar.mother),
          analyzeDoc(r.admission, r.tc),
          analyzeDoc(r.admission, r.marksheet),
          analyzeDoc(r.admission, r.birth_certificate),
        ];
        return checks.some(
          (c) => c.status === "mismatch" || c.status === "missing"
        );
      })
    : rows;

  return (
    <div style={{ padding: "0 4px" }}>
      {/* Toolbar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          marginBottom: 10,
          flexWrap: "wrap",
        }}
      >
        <label
          style={{
            fontSize: 13,
            cursor: "pointer",
            display: "flex",
            gap: 6,
            alignItems: "center",
          }}
        >
          <input
            type="checkbox"
            checked={showIssuesOnly}
            onChange={(e) => setShowIssuesOnly(e.target.checked)}
          />
          Show issues only
        </label>
        <Legend />
      </div>

      {/* Table */}
      <div style={{ overflowX: "auto" }}>
        <table className="table">
          <thead>
            <tr>
              <th>SR</th>
              <th>Student</th>
              <th>Aadhaar</th>
              <th>TC</th>
              <th>Marksheet</th>
              <th>Birth Cert</th>
              <th>Mismatches</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r) => {
              const aS = analyzeDoc(r.admission, r.aadhaar.student);
              const aF = analyzeParentAadhaar(r.admission.father_name, r.aadhaar.father);
              const aM = analyzeParentAadhaar(r.admission.mother_name, r.aadhaar.mother);
              const tc = analyzeDoc(r.admission, r.tc);
              const ms = analyzeDoc(r.admission, r.marksheet);
              const bc = analyzeDoc(r.admission, r.birth_certificate);

              const allIssues = [
                ...aS.issues.map((i) => `AS:${i}`),
                ...aF.issues.map((i) => `AF:${i}`),
                ...aM.issues.map((i) => `AM:${i}`),
                ...tc.issues.map((i) => `TC:${i}`),
                ...ms.issues.map((i) => `MS:${i}`),
                ...bc.issues.map((i) => `BC:${i}`),
              ];

              const isExpanded = expandedSr === r.sr;

              return (
                <React.Fragment key={r.sr}>
                  <tr>
                    <td style={{ fontFamily: "monospace", whiteSpace: "nowrap" }}>
                      {r.sr}
                    </td>
                    <td>
                      <div style={{ fontWeight: 600 }}>
                        {r.admission.student_name}
                      </div>
                      <div style={{ fontSize: 11, color: "#6b7280" }}>
                        {r.admission.dob ?? "—"}
                      </div>
                    </td>

                    {/* Aadhaar column — 3 badges stacked */}
                    <td>
                      <div>
                        <DocBadge label="Student" status={aS.status} issues={aS.issues} />
                      </div>
                      <div>
                        <DocBadge label="Father" status={aF.status} issues={aF.issues} />
                        <DocBadge label="Mother" status={aM.status} issues={aM.issues} />
                      </div>
                    </td>

                    <td>
                      <DocBadge label="TC" status={tc.status} issues={tc.issues} />
                    </td>
                    <td>
                      <DocBadge label="MS" status={ms.status} issues={ms.issues} />
                    </td>
                    <td>
                      <DocBadge label="BC" status={bc.status} issues={bc.issues} />
                    </td>

                    {/* Mismatch summary */}
                    <td style={{ maxWidth: 220 }}>
                      {allIssues.length > 0 ? (
                        <span style={{ fontSize: 11, color: "#991b1b" }}>
                          {allIssues.join(" · ")}
                        </span>
                      ) : (
                        <span style={{ color: "#9ca3af", fontSize: 11 }}>—</span>
                      )}
                    </td>

                    <td>
                      <button
                        className="btn"
                        style={{ fontSize: 11, padding: "2px 8px" }}
                        onClick={() =>
                          setExpandedSr(isExpanded ? null : r.sr)
                        }
                      >
                        {isExpanded ? "Close" : "Compare"}
                      </button>
                    </td>
                  </tr>

                  {isExpanded && (
                    <tr>
                      <td
                        colSpan={8}
                        style={{
                          background: "#f9fafb",
                          padding: "12px 16px",
                        }}
                      >
                        <CompareTable r={r} />
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}

            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} style={{ textAlign: "center", color: "#9ca3af", padding: 24 }}>
                  No records found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
    </div>
  );
}
