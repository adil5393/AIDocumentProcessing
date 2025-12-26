"use client";

import { useEffect, useState } from "react";
import { isLoggedIn, logout } from "../lib/auth";
import { apiFetch } from "../lib/api";
import AdmissionForms from "./Components/AdmissionForms";
import Aadhaars from "./Components/Aadhaars";
import TransferCerts from "./Components/TransferCerts";
import "./Components/dashboard.css";
import Files from "./Components/Files";

type FileRow = {
  file_id: number;
  file_path: string;
  display_name: string;
  doc_type: string;
  ocr_done: boolean;
  extraction_done: boolean;
};
type Tab = "files" | "admission" | "aadhaar" | "tc" ;

export default function Dashboard() {
  const [running, setRunning] = useState(false);
  const [tab, setTab] = useState<Tab>("files");
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState("");
  const [files, setFiles] = useState<FileRow[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);

  function exportExcel() {
    apiFetch("http://localhost:8000/api/export/student-documents.xlsx")
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
    const res = await apiFetch("http://localhost:8000/api/files");
    const data = await res.json();
    setFiles(data);
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
    const res = await apiFetch("http://localhost:8000/api/files");
    const data: FileRow[] = await res.json();

    setFiles(data);

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

  const handleUpload = async () => {
    if (!file) {
      setStatus("No file selected");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setStatus("Uploading...");

    try {
      const res = await apiFetch("http://localhost:8000/api/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        setStatus("Upload failed");
        return;
      }

      setStatus("Upload successful ✅");
      setFile(null);
      loadFiles();
    } catch {
      setStatus("Upload error");
    }
  };

  const runPipeline = async () => {
    setStatus("Running OCR + extraction...");
    setRunning(true);

    await apiFetch("http://localhost:8000/api/ocr/run", {
      method: "POST",
    });

    // start polling
  };


  return (
    <div className="dashboard">
      <h1>Dashboard</h1>

      <input
        type="file"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
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

      </div>

      <div>
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
      </div>
        {tab === "files" && (
            <Files files={files} reloadFiles={loadFiles} />
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
