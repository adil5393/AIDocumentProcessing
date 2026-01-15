"use client";

import { useState, useEffect } from "react";
import { apiFetch } from "../../lib/api";
import "./dashboard.css";
import FilesLockButton from "../LockButton/FileLockButton";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

type FilesProps = {
  openLayover: (file: FileRow) => void;
  search: string;
  active:boolean;
};

type FileRow = {
  file_id: number;
  file_path: string;
  display_name: string;
  doc_type: string;
  ocr_done: boolean;
  extracted_raw: Record<string, any> | null;
  extraction_done: boolean;
  extraction_error: string | null;
  unlock: boolean;
};

export default function Files({openLayover,search, active
}: FilesProps) {
  const [files, setFiles] = useState<FileRow[]>([]);
  const [polling, setPolling] = useState(false);

  const loadFiles = async () => {
    const res = await apiFetch(`${API_BASE}/api/files`);
    const data: FileRow[] = await res.json();
    setFiles(data);
  };
  useEffect(() => {
    loadFiles();
  }, []);

  useEffect(() =>{
  const lock = apiFetch(
          `${API_BASE}/api/files/lock-all`,
          { method: "POST" }
        );
    },[active])
  useEffect(() => {
    if (!polling) return;

    const interval = setInterval(async () => {
      const res = await apiFetch(`${API_BASE}/api/files`);
      const data: FileRow[] = await res.json();
      setFiles(data);

      const allDone =
        data.length > 0 &&
        data.every(f => f.ocr_done && f.extraction_done);

      if (allDone) {
        setPolling(false);
        clearInterval(interval);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [polling]);
  useEffect(() => {
  const hasPending = files.some(
    f => !f.ocr_done || !f.extraction_done
  );

  if (hasPending) {
    setPolling(true);
  }
}, [files]);
const deleteFile = async (id: number) => {
  if (!confirm("Delete this file?")) return;

  await apiFetch(`${API_BASE}/api/files/${id}`, {
    method: "DELETE",
  });

  loadFiles();
};
  return (
    <table className="table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Doc Type</th>
          <th>OCR</th>
          <th>Extraction</th>
          <th>Action</th>
          <th>Unlock To Delete</th>
        </tr>
      </thead>
      <tbody>
       
        {files.map((f) => { 
          return (
          <tr key={f.file_id}>
            <td>{f.display_name}</td>
            <td>{f.doc_type}</td>
            <td>{f.ocr_done ? "✓" : "⏳"}</td>
            <td>
              {f.extraction_error ? (
                <button
                  className="btn"
                  onClick={() => openLayover(f)}
                >
                  ❌ Error
                </button>
              ) : f.extraction_done ? (
                "✓"
              ) : (
                "⏳"
              )}
            </td>
            <td>
              {(f.extraction_error || f.unlock) &&<button
                className="btn"
                onClick={()=>{deleteFile(f.file_id)}}
              >
                Delete
              </button>}
            </td>
            <td>
  <FilesLockButton
    unlocked={f.unlock}
    onUnlock={async () => {
      const password = prompt("Enter password");
      if (!password) return;

      const res = await apiFetch(
        `${API_BASE}/api/unlock/${password}/edit`,
        { method: "POST" }
      );

      if (!res.ok) {
        alert("Invalid password");
        return;
      }

      await apiFetch(
        `${API_BASE}/api/files/${f.file_id}/unlock`,
        { method: "POST" }
      );

      loadFiles(); // ← refresh from backend
    }}
    onLock={async () => {
      await apiFetch(
        `${API_BASE}/api/files/${f.file_id}/lock`,
        { method: "POST" }
      );

      loadFiles(); // ← refresh from backend
    }}
  />
</td>

          </tr>
        )})}
      </tbody>
    </table>
  );
}
