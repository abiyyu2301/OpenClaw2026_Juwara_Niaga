import type { Lead } from "../lib/api";

const STATUS_GROUPS: { key: string; label: string; statuses: string[] }[] = [
  { key: "new", label: "New", statuses: ["new"] },
  { key: "researching", label: "Researching", statuses: ["profiling", "profiled", "debating"] },
  { key: "qualified", label: "Qualified", statuses: ["qualified"] },
  { key: "outreach", label: "Outreach sent", statuses: ["outreach_sent"] },
  { key: "warm", label: "Replied / warm", statuses: ["replied", "warm"] },
  { key: "closing", label: "Closing", statuses: ["closing", "payment_pending"] },
  { key: "paid", label: "Paid", statuses: ["paid"] },
  { key: "lost", label: "Lost / disqualified", statuses: ["lost", "disqualified", "do_not_contact"] },
];

const STATUS_BG: Record<string, string> = {
  new: "bg-sandstone-100",
  researching: "bg-blue-50",
  qualified: "bg-emerald-50",
  outreach: "bg-violet-50",
  warm: "bg-amber-50",
  closing: "bg-orange-50",
  paid: "bg-green-100",
  lost: "bg-red-50",
};

export function LeadKanban({
  leads,
  activeLeadId,
  onSelect,
}: {
  leads: Lead[];
  activeLeadId?: number | null;
  onSelect?: (lead: Lead) => void;
}) {
  return (
    <div className="grid grid-cols-2 gap-2">
      {STATUS_GROUPS.map((g) => {
        const inGroup = leads.filter((l) => g.statuses.includes(l.status));
        if (inGroup.length === 0) return null;
        return (
          <div
            key={g.key}
            className={`rounded-md border border-sandstone-200 ${STATUS_BG[g.key]} p-2`}
          >
            <div className="text-[11px] uppercase tracking-wider text-sandstone-600 mb-1">
              {g.label} <span className="text-sandstone-400">· {inGroup.length}</span>
            </div>
            <ul className="space-y-1">
              {inGroup.map((l) => (
                <li
                  key={l.id}
                  className={`rounded bg-white px-2 py-1.5 text-sm cursor-pointer hover:ring-1 hover:ring-terracotta-300 ${
                    activeLeadId === l.id ? "ring-2 ring-terracotta-500" : ""
                  }`}
                  onClick={() => onSelect?.(l)}
                >
                  <div className="font-medium text-sandstone-900 truncate">{l.company_name}</div>
                  {l.buyer_name && (
                    <div className="text-xs text-sandstone-500 truncate">{l.buyer_name}</div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </div>
  );
}
