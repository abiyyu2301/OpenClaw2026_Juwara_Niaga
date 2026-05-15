/** Multi-select from preset options; values stored joined by separator. */

import { useI18n } from "../lib/i18n";

interface MultiSelectChipsProps {
  label: string;
  hint?: string;
  options: string[];
  value: string;
  onChange: (joined: string) => void;
  separator?: string;
}

export function parseMultiValue(value: string, separator: string): string[] {
  if (!value?.trim()) return [];
  return value.split(separator).map((s) => s.trim()).filter(Boolean);
}

export function joinMultiValue(items: string[], separator: string): string {
  return items.join(separator);
}

export function MultiSelectChips({
  label,
  hint,
  options,
  value,
  onChange,
  separator = " · ",
}: MultiSelectChipsProps) {
  const { t } = useI18n();
  const selected = parseMultiValue(value, separator);

  function toggle(opt: string) {
    const next = selected.includes(opt)
      ? selected.filter((x) => x !== opt)
      : [...selected, opt];
    onChange(joinMultiValue(next, separator));
  }

  return (
    <div className="block">
      <span className="block text-sm font-medium text-stone-800 mb-0.5">{label}</span>
      {hint && <p className="text-xs text-stone-500 mb-2">{hint}</p>}
      <p className="text-xs text-stone-500 mb-2">{t("pick_multiple")}</p>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => {
          const on = selected.includes(opt);
          return (
            <button
              key={opt}
              type="button"
              onClick={() => toggle(opt)}
              className={`text-sm px-3 py-1.5 rounded-full border transition-colors ${
                on
                  ? "bg-stone-900 text-white border-stone-900"
                  : "bg-white text-stone-700 border-stone-300 hover:border-stone-500"
              }`}
            >
              {on ? "✓ " : ""}
              {opt}
            </button>
          );
        })}
      </div>
      {selected.length > 0 && (
        <p className="text-xs text-stone-500 mt-2">
          {t("selected")}: {selected.join(", ")}
        </p>
      )}
    </div>
  );
}
