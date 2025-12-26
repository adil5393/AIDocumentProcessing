"use client";

type Props = {
  label: string;
  value: any;
};

export default function SignalBadge({ label, value }: Props) {
  if (value === null || value === undefined) return null;

  let display = value;
    let cls = "signal-badge signal-weak";

  if (typeof value === "number") {
    if (value > 0.7) cls = "signal-badge signal-strong";
    else if (value > 0.4) cls = "signal-badge signal-medium";
  }

  return (
    <span className={cls}>
      {label}: {typeof value === "number" ? value.toFixed(2) : String(value)}
    </span>
  );
}
