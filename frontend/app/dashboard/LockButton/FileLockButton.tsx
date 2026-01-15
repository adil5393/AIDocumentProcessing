import { Lock, Unlock } from "lucide-react";


export default function FilesLockButton({
  unlocked,
  onUnlock,
  onLock,
}: {
  unlocked: boolean;
  onUnlock: () => Promise<void>;
  onLock: () => Promise<void>;
}) {
  return (
    <button
      type="button"
      className={`lock-btn ${unlocked ? "unlocked" : "locked"}`}
      onClick={unlocked ? onLock : onUnlock}
      aria-pressed={unlocked}
    >
      {unlocked ? <Unlock size={14} /> : <Lock size={14} />}
      <span className="lock-label">
        {unlocked ? "Unlocked" : "Locked"}
      </span>
    </button>
  );
}