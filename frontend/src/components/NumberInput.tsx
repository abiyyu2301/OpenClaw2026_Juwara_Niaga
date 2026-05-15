/** Numeric input with Indonesian thousand separators (e.g. 10.000.000). */

interface NumberInputProps {
  value: number | undefined;
  onChange: (n: number) => void;
  placeholder?: string;
  className?: string;
  min?: number;
}

export function formatIdNumber(n: number | undefined): string {
  if (n === undefined || n === null || Number.isNaN(n)) return "";
  if (n === 0) return "0";
  return n.toLocaleString("id-ID");
}

export function parseIdNumber(raw: string): number {
  const digits = raw.replace(/\D/g, "");
  if (!digits) return 0;
  return parseInt(digits, 10);
}

export function NumberInput({
  value,
  onChange,
  placeholder,
  className = "input",
  min = 0,
}: NumberInputProps) {
  return (
    <input
      type="text"
      inputMode="numeric"
      className={className}
      placeholder={placeholder}
      value={formatIdNumber(value)}
      onChange={(e) => {
        const n = parseIdNumber(e.target.value);
        onChange(Math.max(min, n));
      }}
    />
  );
}
