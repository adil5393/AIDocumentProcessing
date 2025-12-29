"use client";

import DocumentImageViewer from "./DocumentImageViewer";

interface DocumentPreviewRowProps {
  fileId: number;
  colSpan: number;
  apiBase: string;
}

export default function DocumentPreviewRow({
  fileId,
  colSpan,
  apiBase,
}: DocumentPreviewRowProps) {
  return (
    <tr>
      <td colSpan={colSpan}>
        <div
          style={{
            border: "1px solid #ccc",
            marginTop: 8,
            padding: 8,
            background: "#fafafa",
          }}
        >
          <DocumentImageViewer
            src={`${apiBase}/api/files/${fileId}/preview-image`}
          />
        </div>
      </td>
    </tr>
  );
}
