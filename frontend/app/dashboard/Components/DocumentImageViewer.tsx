"use client";

import { useState } from "react";
import './Documentviewer.css'
import ZoomButtons from "../Utils/ZoomButtons";
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
  const [zoom,setZoom] = useState(1)

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
      
    <ZoomButtons zoom={zoom} setZoom={setZoom} />
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
