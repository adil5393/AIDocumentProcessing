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
  const [uploadedFiles, setUploadedFiles] = useState<FileRow[]>([]);
  const [layoverFile, setLayoverFile] = useState<FileRow | null>(null);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);

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
  const loadFiles = async () => {
    const res = await apiFetch(`${API_BASE}/api/files`);
    const data: FileRow[] = await res.json();
    setUploadedFiles(data);
  };

  useEffect(() => {
    if (!isLoggedIn()) {
      window.location.href = "/login";
      return;
    }

    loadFiles();
  }, []);
 useEffect(() => {
  if (!running) return;

  const interval = setInterval(async () => {
    const res = await apiFetch(`${API_BASE}/api/files`);
    const data: FileRow[] = await res.json();

    setUploadedFiles(data);

    const allDone =
      data.length > 0 &&
      data.every(f => f.ocr_done && f.extraction_done);

    if (allDone) {
      setRunning(false);
      setStatus("Pipeline completed ✅");
      clearInterval(interval);
    }
  }, 1500);

  return () => clearInterval(interval);
}, [running]);
useEffect(() => {
  console.log("layoverFile", layoverFile);
}, [layoverFile]);

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
      setStatus("Upload failed");
      return;
    }

    setStatus("Upload successful ✅");
    setSelectedFiles([]);
    loadFiles();
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
<div className="tabs">
  <button className={`tab ${tab === "files" ? "active" : ""}`} onClick={() => setTab("files")}>
    Files
  </button>
  <button className={`tab ${tab === "admission" ? "active" : ""}`} onClick={() => setTab("admission")}>
    Admission Forms
  </button>
  <button className={`tab ${tab === "aadhaar" ? "active" : ""}`} onClick={() => setTab("aadhaar")}>
    Aadhaar
  </button>
  <button className={`tab ${tab === "tc" ? "active" : ""}`} onClick={() => setTab("tc")}>
    Transfer Certificates
  </button>
  <button className={`tab ${tab === "marksheets" ? "active" : ""}`} onClick={() => setTab("marksheets")}>
    Marksheets
  </button>
  <button className={`tab ${tab === "birth_certificates" ? "active" : ""}`} onClick={() => setTab("birth_certificates")}>
    Birth Certificates
  </button>
  <button className={`tab ${tab === "cross_review" ? "active" : ""}`} onClick={() => setTab("cross_review")}>
    Cross Review
  </button>
  
</div>


      <div>
        {layoverFile &&  (
         <AdmissionLayoverModal
  fileId={layoverFile.file_id}
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
          <AdmissionForms />
        )}
        {tab === "aadhaar" && (
          <Aadhaars
            selectedDocId={selectedDocId}
            onSelectDoc={(docId: number) =>
              setSelectedDocId(docId === selectedDocId ? null : docId)
            }
          />
        )}
        {tab === "tc" && <TransferCerts />}
        {tab === "cross_review" && <CrossReview />}
        {tab === "marksheets" && <Marksheets API_BASE={API_BASE}/>}
        {tab === "birth_certificates" && <BirthCertificates API_BASE={API_BASE}/>}
      </div>
        {tab === "files" && (
          <Files
            files={uploadedFiles}
            reloadFiles={loadFiles}
            openLayover={(file) => setLayoverFile(file)}
          />
        )}
      <br />
       
    </div>
  );
}
