"use client";

import { useEffect, useState } from "react";
import { isLoggedIn, logout } from "../lib/auth";
import { apiFetch } from "../lib/api";
import AdmissionForms from "./Components/AdmissionForms";
import Aadhaars from "./Components/Aadhaars";
import TransferCerts from "./Components/TransferCerts";
import "./Components/dashboard.css";
import Files from "./Components/Files";
import AmtechPanel from "./Components/AmtechPanel";
import AdmissionLayoverModal from "./Components/AdmissionLayoverModal";
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
type Tab = "files" | "admission" | "aadhaar" | "tc" | "amtech";

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
      <h1>Dashboard</h1>

      <input
        type="file"
        multiple
        onChange={(e) => {
          if (e.target.files) {
            setSelectedFiles(Array.from(e.target.files));
          }
        }}
      />
      <br /><br />

      <button onClick={handleUpload}>Upload</button>
      <button className="btn"   onClick={runPipeline} style={{ marginLeft: 10 }}>
        Run OCR + Extraction
      </button>

      <p>{status}</p>

      <hr />

      <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
        <button onClick={() => setTab("files")}>Files</button>
        <button onClick={() => setTab("admission")}>Admission Forms</button>
        <button onClick={() => setTab("aadhaar")}>Aadhaar</button>
        <button onClick={() => setTab("tc")}>Transfer Certificates</button>
        <button onClick={() => setTab("amtech")}>Amtech</button>
      </div>

      <div>
        {layoverFile &&  (
          <AdmissionLayoverModal
            fileId={layoverFile.file_id}
            initialData={layoverFile.extracted_raw ?? {}}
            error={layoverFile.extraction_error}
            onConfirm={(data) => {
              // backend confirm endpoint
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
        {tab === "amtech" && <AmtechPanel />}
      </div>
        {tab === "files" && (
          <Files
            files={uploadedFiles}
            reloadFiles={loadFiles}
            openLayover={(file) => setLayoverFile(file)}
          />
        )}
      <br />
      <button
        className="btn"
        onClick={exportExcel}
        style={{ marginBottom: 12 }}
      >
        📥 Export Student Comparison (Excel)
      </button>
      <button className="btn" onClick={logout}>Logout</button>
    </div>
  );
}
