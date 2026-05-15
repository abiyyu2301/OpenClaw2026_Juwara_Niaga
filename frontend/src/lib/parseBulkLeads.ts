/** Parse pasted lines into lead rows for bulk import. */

export interface ParsedLeadRow {
  company_name: string;
  email?: string;
  buyer_name?: string;
}

/**
 * Supported formats per line:
 *   email@company.com
 *   Nama PT <email@company.com>
 *   Nama PT, email@company.com
 *   Nama PT; email@company.com
 */
export function parseBulkLeadLines(text: string): ParsedLeadRow[] {
  const rows: ParsedLeadRow[] = [];
  for (const line of text.split(/\r?\n/)) {
    const raw = line.trim();
    if (!raw || raw.startsWith("#")) continue;

    const angle = raw.match(/^(.+?)\s*<([^>]+@[^>]+)>$/);
    if (angle) {
      rows.push({
        company_name: angle[1].trim(),
        email: angle[2].trim().toLowerCase(),
      });
      continue;
    }

    if (raw.includes(",") || raw.includes(";")) {
      const sep = raw.includes(";") ? ";" : ",";
      const parts = raw.split(sep).map((p) => p.trim());
      const emailPart = parts.find((p) => p.includes("@"));
      const namePart = parts.find((p) => !p.includes("@")) || parts[0];
      rows.push({
        company_name: namePart || emailPart?.split("@")[0] || "Prospek",
        email: emailPart?.toLowerCase(),
      });
      continue;
    }

    if (raw.includes("@")) {
      const local = raw.split("@")[0];
      const name =
        local.replace(/[._-]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()) || "Prospek";
      rows.push({ company_name: name, email: raw.toLowerCase() });
      continue;
    }

    rows.push({ company_name: raw });
  }
  return rows;
}
