"use client";

import { useEffect, useState } from "react";
import { isLoggedIn, logout } from "../lib/auth";
import { apiFetch } from "../lib/api";

export default function Dashboard() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState("");
  const [files, setFiles] = useState<any[]>([]);

  useEffect(() => {
    if (!isLoggedIn()) {
      window.location.href = "/login";
      return;
    }
    apiFetch("http://localhost:8000/api/uploads")
  .then(res => res.json())
  .then(data => setFiles(data));

    apiFetch("http://localhost:8000/api/me")
      .then(res => res.json())
      .then(data => console.log("ME:", data));
  }, []);

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
        // ⚠️ DO NOT set Content-Type manually for FormData
      });

      if (!res.ok) {
        setStatus("Upload failed");
        return;
      }

      setStatus("Upload successful ✅");
    } catch (err) {
      setStatus("Upload error");
    }
  };

  return (
    <div style={{ maxWidth: 500, margin: "50px auto" }}>
      <h1>Dashboard</h1>

      <input
        type="file"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <br /><br />

      <button onClick={handleUpload}>Upload</button>

      <p>{status}</p>

      <hr />

      <button onClick={logout}>Logout</button>
      <h3>Uploaded Files</h3>

      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        {files.map((f) => {
          const url = `http://localhost:8000/api/uploads/${f.filename}`;
          const isImage = /\.(png|jpg|jpeg|webp)$/i.test(f.filename);
          const isPDF = /\.pdf$/i.test(f.filename);

          return (
            <div
              key={f.filename}
              style={{ border: "1px solid #ccc", padding: 10 }}
            >
              {isImage && (
                <img
                  src={url}
                  alt={f.filename}
                  style={{ maxWidth: "100%", maxHeight: 300 }}
                />
              )}

              {isPDF && (
                <iframe
                  src={url}
                  width="100%"
                  height="400"
                  title={f.filename}
                />
              )}

              {!isImage && !isPDF && (
                <a href={url} target="_blank" rel="noopener noreferrer">
                  {f.filename}
                </a>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
