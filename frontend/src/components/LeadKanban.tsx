import type { Lead } from "../lib/api";
import { useI18n } from "../lib/i18n";

const STATUS_KEYS = [
  { key: "new", labelKey: "kanban_new" as const, statuses: ["new"] },
  { key: "researching", labelKey: "kanban_researching" as const, statuses: ["profiling", "profiled", "debating"] },
  { key: "qualified", labelKey: "kanban_qualified" as const, statuses: ["qualified"] },
  { key: "outreach", labelKey: "kanban_outreach" as const, statuses: ["outreach_sent"] },
  { key: "warm", labelKey: "kanban_warm" as const, statuses: ["replied", "warm"] },
  { key: "closing", labelKey: "kanban_closing" as const, statuses: ["closing", "payment_pending"] },
  { key: "paid", labelKey: "kanban_paid" as const, statuses: ["paid"] },
  { key: "lost", labelKey: "kanban_lost" as const, statuses: ["lost", "disqualified", "do_not_contact"] },
];

const STATUS_BG: Record<string, string> = {
  new: "bg-stone-50",
  researching: "bg-blue-50",
  qualified: "bg-emerald-50",
  outreach: "bg-violet-50",
  warm: "bg-amber-50",
  closing: "bg-orange-50",
  paid: "bg-green-50",
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
  const { t } = useI18n();

  return (
    <div className="grid grid-cols-2 gap-2">
      {STATUS_KEYS.map((g) => {
        const inGroup = leads.filter((l) => g.statuses.includes(l.status));
        if (inGroup.length === 0) return null;
        return (
          <div
            key={g.key}
            className={`rounded-lg border border-stone-200 ${STATUS_BG[g.key]} p-2`}
          >
            <div className="text-[11px] uppercase tracking-wider text-stone-600 mb-1 font-medium">
              {t(g.labelKey)} <span className="text-stone-400">· {inGroup.length}</span>
            </div>
            <ul className="space-y-1">
              {inGroup.map((l) => (
                <li
                  key={l.id}
                  className={`rounded-md bg-white px-2 py-1.5 text-sm cursor-pointer border border-stone-100 hover:border-stone-300 ${
                    activeLeadId === l.id ? "ring-2 ring-stone-900 border-stone-300" : ""
                  }`}
                  onClick={() => onSelect?.(l)}
                >
                  <div className="font-medium text-stone-900 truncate">{l.company_name}</div>
                  {l.buyer_name && (
                    <div className="text-xs text-stone-500 truncate">{l.buyer_name}</div>
                  )}
                  {l.email && (
                    <div className="text-[10px] text-stone-400 truncate">{l.email}</div>
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
