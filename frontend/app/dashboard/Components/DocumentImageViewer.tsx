"use client";

import { useState } from "react";
import './documentviewer.css'
interface DocumentImageViewerProps {
  src: string;
  maxHeight?: number;
  background?: string;
}

export default function DocumentImageViewer({
  src,
  maxHeight = 500,
  background = "#111",
}: DocumentImageViewerProps) {
  const [zoom, setZoom] = useState(1);

  return (
    <div
      style={{
        maxHeight,
        overflow: "auto",
        border: "1px solid #ccc",
        background,
        padding: 8,
      }}
    >
      <div className="doc-viewer-toolbar">
        <button className="btn ghost" onClick={() => setZoom(z => Math.min(z + 0.1, 2))}>+</button>
        <button className="btn ghost" onClick={() => setZoom(z => Math.max(z - 0.1, 0.5))}>−</button>
        <button className="btn ghost" onClick={() => setZoom(1)}>Reset</button>
      </div>

      <img
        src={src}
        alt="Document preview"
        style={{
          width: "100%",
          transform: `scale(${zoom})`,
          transformOrigin: "top left",
          transition: "transform 0.15s ease",
          display: "block",
        }}
      />
    </div>
  );
}
