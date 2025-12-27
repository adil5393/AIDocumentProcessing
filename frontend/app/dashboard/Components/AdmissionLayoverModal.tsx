"use client";
import { useState } from "react";
import { apiFetch } from "../../lib/api";
const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;
type AdmissionData = {
  sr: string;
  class: string;
  student_name: string;
  gender: string;
  date_of_birth: string;
  father_name: string;
  mother_name: string;
  address: string;
  phone1: string;
  student_aadhaar_number: string;
};

type Props = {
  fileId: number;
  initialData: Partial<AdmissionData>;
  error: string | null;
  onConfirm: (data: AdmissionData) => void;
  onReject: () => void;
  onClose: () => void;
};

export default function AdmissionLayoverModal({
  fileId,
  initialData,
  error,
  onConfirm,
  onReject,
  onClose,
}: Props) {
  const [form, setForm] = useState<AdmissionData>({
    sr: initialData.sr || "",
    class: initialData.class || "",
    student_name: initialData.student_name || "",
    gender: initialData.gender || "",
    date_of_birth: initialData.date_of_birth || "",
    father_name: initialData.father_name || "",
    mother_name: initialData.mother_name || "",
    address: initialData.address || "",
    phone1: initialData.phone1 || "",
    student_aadhaar_number: initialData.student_aadhaar_number || "",
  });

  const set = (k: keyof AdmissionData, v: string) =>
    setForm(p => ({ ...p, [k]: v }));

 return (
  <div className="layover-backdrop">
    <div className="layover-modal split">

      {/* LEFT: Document Preview */}
      <div className="doc-preview">
        <iframe
          src={`${API_BASE}/api/files/${fileId}/preview`}
          title="Document Preview"
        />
      </div>

      {/* RIGHT: Review Panel */}
      <div className="review-panel">

        <h2 className="modal-title">Admission Form Review</h2>

        {error && (
          <div className="warning-box">
            ⚠️ {error}
          </div>
        )}

        <div className="form-grid">
          <label>SR</label>
          <input value={form.sr} onChange={e => set("sr", e.target.value)} />

          <label>Class</label>
          <input value={form.class} onChange={e => set("class", e.target.value)} />

          <label>Student Name</label>
          <input value={form.student_name} onChange={e => set("student_name", e.target.value)} />

          <label>Gender</label>
          <select value={form.gender} onChange={e => set("gender", e.target.value)}>
            <option value="">--</option>
            <option>Male</option>
            <option>Female</option>
          </select>

          <label>Date of Birth</label>
          <input
            type="date"
            value={form.date_of_birth}
            onChange={e => set("date_of_birth", e.target.value)}
          />

          <label>Father Name</label>
          <input value={form.father_name} onChange={e => set("father_name", e.target.value)} />

          <label>Mother Name</label>
          <input value={form.mother_name} onChange={e => set("mother_name", e.target.value)} />

          <label>Address</label>
          <textarea value={form.address} onChange={e => set("address", e.target.value)} />

          <label>Phone</label>
          <input value={form.phone1} onChange={e => set("phone1", e.target.value)} />

          <label>Student Aadhaar</label>
          <input
            value={form.student_aadhaar_number}
            onChange={e => set("student_aadhaar_number", e.target.value)}
          />
        </div>

        <div className="layover-actions">
          <button className="btn secondary" onClick={onClose}>
            Cancel
          </button>

          <button
            className="btn primary"
            onClick={async () => {
              await apiFetch(`${API_BASE}/api/files/${fileId}/reassess`, {
                method: "POST",
                body: JSON.stringify({ extracted_raw: form }),
              });
onConfirm(form);
onClose()
            }}
          >
            ✅ Fix & Reprocess
          </button>

          <button className="btn danger" onClick={onReject}>
            ❌ Mark Invalid
          </button>
        </div>

      </div>
    </div>
  </div>
);
}