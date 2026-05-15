/** Dropdown with preset options + manual "Other" text field. */

import { useEffect, useState } from "react";
import { useI18n } from "../lib/i18n";

interface ComboFieldProps {
  label: string;
  hint?: string;
  placeholder?: string;
  options: string[];
  otherLabel?: string;
  value: string;
  onChange: (v: string) => void;
}

export function ComboField({
  label,
  hint,
  placeholder,
  options,
  otherLabel: otherLabelProp,
  value,
  onChange,
}: ComboFieldProps) {
  const { t } = useI18n();
  const otherLabel = otherLabelProp ?? t("other_label");
  const hasOther = options.includes(otherLabel);
  const isCustom = value && !options.includes(value);
  const [mode, setMode] = useState<"preset" | "other">(
    isCustom || value === otherLabel ? "other" : "preset",
  );
  const [otherText, setOtherText] = useState(isCustom ? value : "");

  useEffect(() => {
    if (isCustom) {
      setMode("other");
      setOtherText(value);
    } else if (options.includes(value)) {
      setMode(value === otherLabel ? "other" : "preset");
    }
  }, [value, isCustom, options, otherLabel]);

  const selectVal =
    mode === "other" || value === otherLabel || isCustom
      ? hasOther
        ? otherLabel
        : ""
      : options.includes(value)
      ? value
      : "";

  return (
    <label className="block">
      <span className="block text-sm font-medium text-stone-800 mb-0.5">{label}</span>
      {hint && <p className="text-xs text-stone-500 mb-1">{hint}</p>}
      <select
        className="input"
        value={selectVal}
        onChange={(e) => {
          const v = e.target.value;
          if (v === otherLabel && hasOther) {
            setMode("other");
            onChange(otherText.trim() || otherLabel);
          } else if (v) {
            setMode("preset");
            setOtherText("");
            onChange(v);
          } else {
            setMode("preset");
            onChange("");
          }
        }}
      >
        <option value="">{t("select_placeholder")}</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
      {hasOther && (selectVal === otherLabel || mode === "other") && (
        <input
          className="input mt-2"
          placeholder={placeholder || t("ph_other")}
          value={otherText}
          onChange={(e) => {
            const next = e.target.value;
            setOtherText(next);
            setMode("other");
            onChange(next.trim() || otherLabel);
          }}
          autoFocus={selectVal === otherLabel && !otherText}
        />
      )}
    </label>
  );
}
