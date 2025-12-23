"use client";

import { useEffect, useState } from "react";
import { isLoggedIn, logout } from "../lib/auth";
import { apiFetch } from "../lib/api";
import AdmissionForms from "./AdmissionForms";
import Aadhaars from "./Aadhaars";
import TransferCerts from "./TransferCerts";

type FileRow = {
  file_id: number;
  file_path: string;
  display_name: string;
  doc_type: string;
  ocr_done: boolean;
  extraction_done: boolean;
};
type Tab = "files" | "admission" | "aadhaar" | "tc";



export default function Dashboard() {
  const [running, setRunning] = useState(false);
  const [tab, setTab] = useState<Tab>("files");
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState("");
  const [files, setFiles] = useState<FileRow[]>([]);


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
    <div style={{ maxWidth: 600, margin: "50px auto" }}>
      <h1>Dashboard</h1>

      <input
        type="file"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <br /><br />

      <button onClick={handleUpload}>Upload</button>
      <button onClick={runPipeline} style={{ marginLeft: 10 }}>
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
        {tab === "aadhaar" && <Aadhaars />}
        {tab === "tc" && <TransferCerts />}
      </div>
        {tab === "files" && (
          <table width="100%" border={1} cellPadding={6}>
            <thead>
              <tr>
                <th>Name</th>
                <th>Doc Type</th>
                <th>OCR</th>
                <th>Extraction</th>
              </tr>
            </thead>
            <tbody>
              {files.map((f) => (
                <tr key={f.file_id}>
                  
                  <td>{f.display_name}</td>
                  <td>{f.doc_type}</td>
                  <td>{f.ocr_done ? "✓" : "⏳"}</td>
                  <td>{f.extraction_done ? "✓" : "⛔"}</td>
                  <td>
                    {(
                      <button
                        onClick={async () => {
                          if (!confirm("Delete this file?")) return;

                          await apiFetch(
                            `http://localhost:8000/api/files/${f.file_id}`,
                            { method: "DELETE" }
                          );

                          loadFiles();
                        }}
                      >
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
          </tbody>

        </table>
      )}
      <br />
      <button onClick={logout}>Logout</button>
    </div>
  );
}
