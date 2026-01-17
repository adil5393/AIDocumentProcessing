"use client";

import { useState, useEffect } from "react";
import { apiFetch } from "../../lib/api";
import "./dashboard.css";
import FilesLockButton from "../LockButton/FileLockButton";
import { useRef } from "react";
import { usePaginatedApi } from "../Pagination/PaginatedApi";
import { FileSubTab } from "../Tabs/TabGroup";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

type FilesProps = {
  openLayover: (file: FileRow) => void;
  search: string;
  active:boolean;
  subTab:FileSubTab;
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

export default function Files({openLayover,search, active,subTab
}: FilesProps) {
  // const [files, setFiles] = useState<FileRow[]>([]);
  // const [polling, setPolling] = useState(false);
  const {
        items: rows,
        page,
        total,
        pageSize,
        setPage,
        loading,
        refresh
      } = usePaginatedApi<any>(
      `${API_BASE}/api/files?tab=${subTab}`,
      search,
      50,
      [search] // 👈 dependency
    );
  // const fetchId = useRef(0);

//   const loadFiles = async () => {
//   const id = ++fetchId.current;

//   const res = await apiFetch(`${API_BASE}/api/files`);
//   const data = await res.json();

//   if (id !== fetchId.current) return;
//   setFiles(data);
// };
  // useEffect(() => {
  //   loadFiles();
  // }, []);

    const didLockAll = useRef(false);

useEffect(() => {
  if (!active || didLockAll.current) return;

  didLockAll.current = true;
  apiFetch(`${API_BASE}/api/files/lock-all`, { method: "POST" });
  refresh();
}, [active, refresh]);

//   useEffect(() => {
//   if (!polling) return;

//   const interval = setInterval(async () => {
//     await loadFiles();

//     const allDone =
//       files.length > 0 &&
//       files.every(f => f.ocr_done && f.extraction_done);

//     if (allDone) {
//       setPolling(false);
//     }
//   }, 1500);

//   return () => clearInterval(interval);
// }, [polling]);
//  useEffect(() => {
//   const hasPending = rows.some(
//     f => !f.ocr_done || !f.extraction_done
//   );

//   if (hasPending && !polling) {
//     setPolling(true);
//   }
// }, [files, polling]);
useEffect(() => {
  if (!active) return;

  const hasPending = rows.some(
    f => !f.ocr_done || !f.extraction_done
  );

  if (!hasPending) return;

  const interval = setInterval(() => {
    refresh();
  }, 1500);

  return () => clearInterval(interval);
}, [rows, active, refresh]);

const deleteFile = async (id: number) => {
  if (!confirm("Delete this file?")) return;

  await apiFetch(`${API_BASE}/api/files/${id}`, {
    method: "DELETE",
  });

  // loadFiles();
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
       
        {rows.map((f) => { 
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
              {(f.unlock) &&<button
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

      // loadFiles(); // ← refresh from backend
    }}
    onLock={async () => {
      await apiFetch(
        `${API_BASE}/api/files/${f.file_id}/lock`,
        { method: "POST" }
      );

      // loadFiles(); // ← refresh from backend
    }}
  />
</td>

          </tr>
        )})}
      </tbody>
    </table>
  );
}
