import { useState } from "react";
import { apiFetch } from "../../lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

export default function EditableCell({
  value,
  id,
  field,
  endpoint,
  onSaved
}: {
  value: string | null;
  id: string | number;
  field: string;
  endpoint: string; // e.g. "admission-forms" | "transfer-certificates"
  onSaved: () => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value || "");
  const [saving, setSaving] = useState(false);

  async function save() {
    if (editValue === value) {
      setIsEditing(false);
      return;
    }

    setSaving(true);

    try {
      await apiFetch(
        `${API_BASE}/api/${endpoint}/${id}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ [field]: editValue })
        }
      );

      setIsEditing(false);
      onSaved();
    } catch (err) {
      alert("Failed to save");
      console.error(err);
    } finally {
      setSaving(false);
    }
  }

  if (isEditing) {
    return (
      <input
        autoFocus
        disabled={saving}
        value={editValue}
        onChange={e => {
          const val = e.target.value;

          // 📞 phone validation (still reusable)
          if (field.startsWith("phone") && !/^\d*$/.test(val)) return;

          setEditValue(val);
        }}
        onBlur={save}
        onKeyDown={e => {
          if (e.key === "Enter") save();
          if (e.key === "Escape") {
            setEditValue(value || "");
            setIsEditing(false);
          }
        }}
        style={{ width: "100%" }}
      />
    );
  }

  return (
    <span
      style={{ cursor: "pointer", borderBottom: "1px dashed #ccc" }}
      onClick={() => {
        setEditValue(value || "");
        setIsEditing(true);
      }}
    >
      {value || <i style={{ color: "#aaa" }}>click to edit</i>}
    </span>
  );
}
