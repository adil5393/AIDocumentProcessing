"use client";
import { useState } from "react";
import { apiFetch } from "../../lib/api";
const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;
import { useEffect } from "react";
import ZoomButtons from "../Utils/ZoomButtons";

type DocumentFormData  = {
  //admission_fields
  sr: string;
  class: string;
  student_name: string;
  gender: string;
  date_of_birth: string;
  father_name: string;
  father_aadhaar: string;
  father_occupation: string;
  mother_name: string;
  mother_aadhaar: string;
  mother_occupation: string;
  address: string;
  phone1: string;
  phone2: string;
  student_aadhaar_number: string;
  last_school_attended: string;
  //aadhaar_fields
  name: string | undefined;
  aadhaar_number: string;
  related_name: string;
  relation_type: string;
  //TC fields
  last_class_studied:string;
  last_school_name:string;
  //HighSchool Marksheet
  result_status:string;
  
};

type Props = {
  fileId: number;
  docType: string; 
  initialData: Partial<DocumentFormData >;
  error: string | null;
  onConfirm: (data: Partial<DocumentFormData>) => void;
  onReject: () => void;
  onClose: () => void;
};

type FieldKey = keyof DocumentFormData ;

type FieldDef = {
  key: FieldKey;
  label: string;
  type?: "text" | "date" | "textarea" | "select";
};

const DOC_FIELDS: Record<string, FieldDef[]> = {

  admission_form: [
    { key: "sr", label: "SR" },
    { key: "class", label: "Class" },
    { key: "student_name", label: "Student Name" },
    { key: "gender", label: "Gender", type: "select" },
    { key: "date_of_birth", label: "Date of Birth", type: "date" },

    { key: "father_name", label: "Father Name" },
    { key: "father_aadhaar", label: "Father Aadhaar" },
    { key: "father_occupation", label: "Father Occupation" },

    { key: "mother_name", label: "Mother Name" },
    { key: "mother_aadhaar", label: "Mother Aadhaar" },
    { key: "mother_occupation", label: "Mother Occupation" },

    { key: "address", label: "Address", type: "textarea" },
    { key: "phone1", label: "Phone1" },
    {key: "phone2",label : "Phone2"},

    { key: "student_aadhaar_number", label: "Student Aadhaar" },
    { key: "last_school_attended", label: "Last School Attended" },
  ],

  aadhaar: [
    { key: "name", label: "Name" },
    { key: "date_of_birth", label: "Date of Birth", type: "date" },
    { key: "aadhaar_number", label: "Aadhaar Number" },
    { key: "related_name", label: "Related Person Name" },
    {
      key: "relation_type",
      label: "Relation Type",
      
    },
  ],

  transfer_certificate: [
    { key: "student_name", label: "Student Name" },
    { key: "date_of_birth", label: "Date of Birth", type: "date" },
    { key: "last_school_attended", label: "Last School Attended" },
    { key: "father_name", label: "Father Name" },
    { key: "mother_name", label: "Mother Name" },
  ],

  birth_certificate: [
    { key: "student_name", label: "Name" },
    { key: "date_of_birth", label: "Date of Birth", type: "date" },
    { key: "father_name", label: "Father Name" },
    { key: "mother_name", label: "Mother Name" },
  ],

  marksheet: [
    { key: "student_name", label: "Name" },
    { key: "date_of_birth", label: "Date of Birth", type: "date" },
    { key: "father_name", label: "Father Name" },
    { key: "mother_name", label: "Mother Name" },
  ],
};

export default function LayoverModal({
  fileId,
  docType,
  initialData,
  error,
  onConfirm,
  onReject,
  onClose,
}: Props) {
  const [form, setForm] = useState<Partial<DocumentFormData >>({
    sr: initialData.sr || "",
    class: initialData.class || "",
    student_name: initialData.student_name || "",
    gender: initialData.gender || "",
    date_of_birth: initialData.date_of_birth || "",
    father_name: initialData.father_name || "",
    father_aadhaar: initialData.father_aadhaar || "",
    father_occupation: initialData.father_occupation || "",
    mother_name: initialData.mother_name || "",
    mother_aadhaar: initialData.mother_aadhaar || "",
    mother_occupation: initialData.mother_occupation || "",
    address: initialData.address || "",
    phone1: initialData.phone1 || "",
    student_aadhaar_number: initialData.student_aadhaar_number || "",
    last_school_attended: initialData.last_school_attended || "",
  
  });
  const [selectedDocType, setSelectedDocType] = useState<string>(docType);
  const [zoom,setZoom] = useState(1);

  const set = (k: keyof DocumentFormData, v: string) =>
    setForm(p => ({ ...p, [k]: v }));
  useEffect(() => {
    console.log("Layover initialData:", initialData);
  }, [initialData]);
 return (
  <div className="layover-backdrop">
    <div className="layover-modal split">

      {/* LEFT: Document Preview */}
      <div className="doc-preview">
        <div className="doc-scroll">
          <ZoomButtons zoom={zoom} setZoom={setZoom}/>
          <img
            src={`${API_BASE}/api/files/${fileId}/preview-image`}
            alt="Document Preview"
            className="doc-image"
            style={{
            width: "100%",
            transform: `scale(${zoom})`,
            transformOrigin: "top left",
            transition: "transform 0.15s ease",
            display: "block",
          }}
          />
      </div>
    </div>
 

      {/* RIGHT: Review Panel */}
      <div className="review-panel">

        <h2 className="modal-title">
          {selectedDocType.replace(/_/g, " ").toUpperCase()}
        </h2>

        {error && (
          <div className="warning-box">
            ⚠️ {error}
          </div>
        )}
        
        <div className="form">

  {/* Document type selector */}
  <div className="form-row">
    <label>Document Type</label>
    <select
      value={selectedDocType}
      onChange={e => setSelectedDocType(e.target.value)}
    >
      <option value="admission_form">Admission Form</option>
      <option value="aadhaar">Aadhaar</option>
      <option value="transfer_certificate">Transfer Certificate</option>
      <option value="birth_certificate">Birth Certificate</option>
      <option value="marksheet">High School Marksheet</option>
    </select>
  </div>

  {/* Dynamic fields */}
  {DOC_FIELDS[selectedDocType]?.map(field => (
    <div className="form-row" key={field.key}>
      <label>{field.label}</label>

      {field.type === "textarea" ? (
        <textarea
          value={form[field.key] ?? ""}
          onChange={e => set(field.key, e.target.value)}
        />
      ) : field.type === "select" ? (
        <select
          value={form[field.key] ?? ""}
          onChange={e => set(field.key, e.target.value)}
        >
          <option value="">--</option>
          {field.key === "gender" && (
            <>
              <option>Male</option>
              <option>Female</option>
            </>
          )}
          {field.key === "relation_type" && (
            <>
              <option value="father">Father</option>
              <option value="mother">Mother</option>
              <option value="guardian">Guardian</option>
            </>
          )}
        </select>
      ) : (
        <input
          type={field.type === "date" ? "date" : "text"}
          value={form[field.key] ?? ""}
          onChange={e => set(field.key, e.target.value)}
        />
      )}
    </div>
  ))}

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
                body: JSON.stringify({ doc_type: selectedDocType,extracted_raw: form }),
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