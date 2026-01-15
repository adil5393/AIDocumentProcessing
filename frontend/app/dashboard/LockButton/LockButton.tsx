import { useState } from "react";
import { apiFetch } from "../../lib/api";
import { Lock, Unlock } from "lucide-react";
const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

export default function LockButton({
  rowId,
  unlocked,
  onChange
}: {
  rowId: string | number;
  unlocked: boolean;
  onChange: (state: boolean) => void;
}) {

  const [loading, setLoading] = useState(false);

  async function toggle() {
    if (unlocked) {
      onChange(false);
      return;
    }

    const password = prompt("Enter password to unlock");
    if (!password) return;

    setLoading(true);

    try {
      const res = await apiFetch(
        `${API_BASE}/api/unlock/${password}/edit`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        //   body: JSON.stringify({ password })
        }
      );

      if (!res.ok) {
        alert("Invalid password");
        return;
      }

      onChange(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      className="icon-btn"
      onClick={toggle}
      disabled={loading}
      title={unlocked ? "Lock row" : "Unlock row"}
    >
      {unlocked ? (
        <Unlock size={16} className="lock-icon unlocked" />
      ) : (
        <Lock size={16} className="lock-icon locked" />
      )}
    </button>
  );
}
