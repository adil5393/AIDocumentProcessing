import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";

export default function EditableCell({
  value,
  sr,
  field,
  onSaved
}: {
  value: string;
  sr: string;
  field: string;
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
        `http://localhost:8000/api/admission-forms/${sr}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ [field]: editValue })
        }
      );

      setIsEditing(false);
      onSaved(); // ✅ parent refresh
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

            // 📞 Phone validation
            if (field.startsWith("phone")) {
            if (!/^\d*$/.test(val)) return;
            }

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
    <span style={{ cursor: "pointer", borderBottom: "1px dashed #ccc" }}
      onClick={() => {
        setEditValue(value || "");
        setIsEditing(true);
      }}
    >
      {value || <i style={{ color: "#aaa" }}>click to edit</i>}

    </span>
  );
}
