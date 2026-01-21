"use client";

import { useState, useEffect } from "react";
import { apiFetch } from "../../lib/api";
import "./dashboard.css";
import FilesLockButton from "../LockButton/FileLockButton";
import { useRef } from "react";
import { usePaginatedApi } from "../Pagination/PaginatedApi";
import { FileSubTab } from "../Tabs/TabGroup";
import Pagination from "../Pagination/Pagination";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

type FilesProps = {
  openLayover: (file: FileRow) => void;
  search: string;
  active:boolean;
  subTab:FileSubTab;
  fromDate: string | null;
  toDate: string | null;
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

export default function Files({openLayover,search, active,subTab,fromDate,toDate
}: FilesProps) {
  
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
      [search,fromDate,toDate],
      {
        from_date: fromDate,
        to_date: toDate,
      } // 👈 dependency
    );
    const didLockAll = useRef(false);
    useEffect(() => {
      didLockAll.current = false;
    }, [subTab]);
    useEffect(() => {
      if (!active || didLockAll.current) return;

      didLockAll.current = true;
      apiFetch(`${API_BASE}/api/files/lock-all`, { method: "POST" });
      refresh();
    }, [active, refresh]);
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
   refresh();
  // loadFiles();
};
  return (
  <>
    <table className="table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Doc Type</th>
          <th>OCR</th>
          <th>Extraction</th>
          <th>Action</th>
          <th>Unlock To Delete</th>
          <th>View</th>
          <th>Index</th>
        </tr>
      </thead>
      <tbody>
       
        {rows.map((f,index) => { 
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
              {/* (f.extraction_error || f.unlock) && */}
              {<button
              
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
              refresh();
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
              refresh();
              // loadFiles(); // ← refresh from backend
            }}
          />
        </td>
        <td>
          <button
            className="btn"
            onClick={() =>
              window.open(
                `${API_BASE}/api/files/${f.file_id}/preview-image`,
                "_blank"
              )
            }
          >
            View
          </button>
        </td>
        <td className="btn index" style={{"width":"1%"}}>{index+1}</td>
          </tr>
        )})}
      
      
      
      </tbody>
    </table>
    <Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage}/>
    </>
  );
}
