"use client";

import { useEffect, useState } from "react";
import { isLoggedIn, logout } from "../lib/auth";
import { apiFetch } from "../lib/api";
import AdmissionForms from "./Components/AdmissionForms";
import Aadhaars from "./Components/Aadhaars";
import TransferCerts from "./Components/TransferCerts";
import "./Components/dashboard.css";
import Files from "./Components/Files";
import CrossReview from "./Components/CrossReview";
import AdmissionLayoverModal from "./Components/AdmissionLayoverModal";
import Marksheets from "./Components/Marksheets";
import './Components/header.css'
import BirthCertificates from "./Components/Birthcertificates";
const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

type FileRow = {
  file_id: number;
  file_path: string;
  display_name: string;
  doc_type: string;
  ocr_done: boolean;
  extracted_raw: Record<string, any> | null;
  extraction_done: boolean;
  extraction_error: string | null;
};
type Tab = "files" | "admission" | "aadhaar" | "tc" | "cross_review" | "marksheets" | "birth_certificates";

export default function Dashboard() {
  const [running, setRunning] = useState(false);
  const [tab, setTab] = useState<Tab>("files");
  const [status, setStatus] = useState("");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [layoverFile, setLayoverFile] = useState<FileRow | null>(null);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
  const [search, setSearch] = useState("");

  function exportExcel() {
    apiFetch(`${API_BASE}/api/export/student-documents.xlsx`)
      .then(res => {
        if (!res.ok) throw new Error("Export failed");
        return res.blob();
      })
      .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "student_document_comparison.xlsx";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      })
      .catch(err => {
        alert("Failed to download Excel");
        console.error(err);
      });
  }
  

  useEffect(() => {
    if (!isLoggedIn()) {
      window.location.href = "/login";
      return;
    }
  }, []); 
useEffect(() => {
  console.log("layoverFile", layoverFile);
}, [layoverFile]);
// useEffect(() => {
//   setSearch("");
// }, [tab]);

  const handleUpload = async () => {
  if (selectedFiles.length === 0) {
    setStatus("No files selected");
    return;
  }

  const formData = new FormData();
  selectedFiles.forEach(file => {
    formData.append("files", file);
  });

  setStatus(`Uploading ${selectedFiles.length} files...`);

  try {
    const res = await apiFetch(`${API_BASE}/api/upload`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json();   // 👈 THIS was missing
      setStatus(err.detail || "Upload failed");
      return;
    }

    setStatus("Upload successful ✅");
    setSelectedFiles([]);
  } catch {
    setStatus("Upload error");
  }
};

  const runPipeline = async () => {
    setStatus("Running OCR + extraction...");
    setRunning(true);

    try {
      const res = await apiFetch(`${API_BASE}/api/ocr/run`, {
        method: "POST",
      });

      if (!res.ok) {
        const err = await res.text();
        setRunning(false);
        setStatus(`Pipeline failed ❌: ${err}`);
        return;
      }

      setStatus("Pipeline started 🚀");

    } catch (e) {
      setRunning(false);
      setStatus("Pipeline error ❌");
    }
  };


  return (
    <div className="dashboard">
      <h1 className="dashboard-title">Dashboard</h1>
      <div className="dashboard-header">
{/* ACTION BAR */}
<div className="action-bar">
  <label className="file-picker">
    <input
      type="file"
      multiple
      onChange={(e) => {
        if (e.target.files) {
          setSelectedFiles(Array.from(e.target.files));
        }
      }}
    />
    📂 Choose Files
  </label>

  <button className="btn primary" onClick={handleUpload}>
    ⬆ Upload
  </button>

  <button className="btn secondary" onClick={runPipeline}>
    ⚙ Run OCR + Extraction
  </button>
  <div className="action-right">
        <button className="btn ghost" onClick={exportExcel}>
          📥 Export Excel
        </button>

        <button className="btn danger" onClick={logout}>
          Logout
        </button>
      </div>
  <span className="status-text">{status}</span>
</div>
  

{/* TABS */}

  <div className="tabs-row">
    <div className="tabs">
      <button className={`tab ${tab === "files" ? "active" : ""}`} onClick={() => setTab("files")}>Files</button>
      <button className={`tab ${tab === "admission" ? "active" : ""}`} onClick={() => setTab("admission")}>Admission Forms</button>
      <button className={`tab ${tab === "aadhaar" ? "active" : ""}`} onClick={() => setTab("aadhaar")}>Aadhaar</button>
      <button className={`tab ${tab === "tc" ? "active" : ""}`} onClick={() => setTab("tc")}>Transfer Certificates</button>
      <button className={`tab ${tab === "marksheets" ? "active" : ""}`} onClick={() => setTab("marksheets")}>Marksheets</button>
      <button className={`tab ${tab === "birth_certificates" ? "active" : ""}`} onClick={() => setTab("birth_certificates")}>Birth Certificates</button>
      <button className={`tab ${tab === "cross_review" ? "active" : ""}`} onClick={() => setTab("cross_review")}>Cross Review</button>
    </div>

    {/* SEARCH BAR */}
    <input
      className="tab-search"
      type="text"
      placeholder={
        tab === "admission"
          ? "Search name / SR…"
          : tab === "cross_review"
          ? "Search student…"
          : "Search…"
      }
      value={search}
      onChange={(e) => setSearch(e.target.value)}
    />
  </div>
</div>
      <div>
        {layoverFile &&  (
         <AdmissionLayoverModal
  fileId={layoverFile.file_id} docType={layoverFile.doc_type}
  initialData={
    typeof layoverFile.extracted_raw === "string"
      ? JSON.parse(layoverFile.extracted_raw)
      : layoverFile.extracted_raw ?? {}
  }
  error={layoverFile.extraction_error}
  onConfirm={(data) => {
    console.log("CONFIRM ADMISSION", data);
  }}
  onReject={() => {
    console.log("REJECT ADMISSION");
  }}
  onClose={() => setLayoverFile(null)}
/>
        )}
        {tab === "admission" && (
          <AdmissionForms search={search}/>
        )}
        {tab === "aadhaar" && (
          <Aadhaars
            selectedDocId={selectedDocId}
            search={search}
            onSelectDoc={(docId: number) =>
              setSelectedDocId(docId === selectedDocId ? null : docId)
            }
          />
        )}
        {tab === "tc" && <TransferCerts search={search}/>}
        {tab === "cross_review" && <CrossReview search={search} />}
        {tab === "marksheets" && <Marksheets API_BASE={API_BASE} search = {search}/>}
        {tab === "birth_certificates" && <BirthCertificates API_BASE={API_BASE} search = {search}/>}
      </div>
        {tab === "files" && (
          <Files
            openLayover={(file) => setLayoverFile(file)}
            search = {search}
            active={tab === "files"}
          />
        )}
      <br />
       
    </div>
  );
}
