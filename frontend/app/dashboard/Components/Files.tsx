"use client";

import { apiFetch } from "../../lib/api";
import "./dashboard.css";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

type FileRow = {
  file_id: number;
  file_path: string;
  display_name: string;
  doc_type: string;
  ocr_done: boolean;
  extraction_done: boolean;
};

type FilesProps = {
  files: FileRow[];
  reloadFiles: () => void;
};

export default function Files({ files, reloadFiles }: FilesProps) {
  return (
    <table className="table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Doc Type</th>
          <th>OCR</th>
          <th>Extraction</th>
          <th>Action</th>
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
              <button
                className="btn"
                onClick={async () => {
                  if (!confirm("Delete this file?")) return;

                  await apiFetch(
                    `${API_BASE}/api/files/${f.file_id}`,
                    { method: "DELETE" }
                  );

                  reloadFiles();
                }}
              >
                Delete
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
