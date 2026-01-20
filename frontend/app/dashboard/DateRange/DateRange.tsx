type DateRange = {
  from: string | null;
  to: string | null;
};

type Props = {
  value: DateRange;
  onChange: (value: DateRange) => void;
};

export default function DateRangePicker({ value, onChange }: Props) {
  return (
    <div className="date-range">
      <label>
        From:
        <input
          type="date"
          value={value.from ?? ""}
          onChange={e =>
            onChange({ ...value, from: e.target.value || null })
          }
        />
      </label>

      <label>
        To:
        <input
          type="date"
          value={value.to ?? ""}
          onChange={e =>
            onChange({ ...value, to: e.target.value || null })
          }
        />
      </label>

      <button
        className="btn secondary"
        onClick={() => onChange({ from: null, to: null })}
      >
        Clear
      </button>
    </div>
  );
}
