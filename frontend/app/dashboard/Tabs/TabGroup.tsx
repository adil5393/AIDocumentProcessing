import './tabgroup.css'

export type FileSubTab = "all" | "ocr_error" | "extraction_error";

type TabDef<T extends string> = {
  id: T;
  label: string;
  visible?: boolean;
};

type TabGroupProps<T extends string> = {
  tabs: TabDef<T>[];
  active: T;
  onChange: (tab: T) => void;
};

export default function TabGroup<T extends string>({
  tabs,
  active,
  onChange,
}: TabGroupProps<T>) {
  return (
    <div className="tabs">
      {tabs
        .filter(t => t.visible !== false)
        .map(t => (
          <button
            key={t.id}
            className={`tab ${active === t.id ? "active" : ""}`}
            onClick={() => onChange(t.id)}
          >
            {t.label}
          </button>
        ))}
    </div>
  );
}
