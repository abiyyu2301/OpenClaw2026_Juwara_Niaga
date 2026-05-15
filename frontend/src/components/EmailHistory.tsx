/** Email + payment history for an active lead. */

interface EmailHistoryProps {
  drafts?: any[];
  replies?: any[];
  payments?: any[];
  onSimulatePay?: (ref: string, status: "paid" | "failed" | "expired") => void;
}

function fmtTime(s?: string): string {
  if (!s) return "";
  try {
    const d = new Date(s);
    return d.toLocaleString("en-GB", { hour12: false });
  } catch {
    return s;
  }
}

export function EmailHistory({ drafts = [], replies = [], payments = [], onSimulatePay }: EmailHistoryProps) {
  if (drafts.length === 0 && replies.length === 0 && payments.length === 0) {
    return (
      <div className="rounded-lg border border-sandstone-200 bg-white p-3 text-xs text-sandstone-500">
        No outreach yet. Emails will appear here once the agents send them.
      </div>
    );
  }
  return (
    <div className="space-y-3">
      {drafts.length > 0 && (
        <details open className="rounded-lg border border-l-4 border-l-agent-outreach bg-white p-3">
          <summary className="cursor-pointer text-xs uppercase font-bold text-agent-outreach select-none">
            Outbound emails · {drafts.length}
          </summary>
          <div className="mt-2 space-y-2">
            {drafts.map((d) => (
              <div key={d.id} className="text-xs text-sandstone-800 border-t border-sandstone-100 pt-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold">{d.subject}</span>
                  <span
                    className={`text-[10px] uppercase rounded px-1.5 py-0.5 ${
                      d.status === "sent"
                        ? "bg-emerald-100 text-emerald-800"
                        : d.status === "failed"
                        ? "bg-red-100 text-red-800"
                        : "bg-sandstone-100 text-sandstone-700"
                    }`}
                  >
                    {d.status}
                  </span>
                </div>
                <div className="text-[10px] text-sandstone-500 mt-0.5">
                  {d.draft_type} · {fmtTime(d.sent_at || d.created_at)}
                </div>
                <pre className="whitespace-pre-wrap font-sans text-[11.5px] text-sandstone-700 mt-1 max-h-40 overflow-y-auto">
                  {d.body}
                </pre>
              </div>
            ))}
          </div>
        </details>
      )}

      {replies.length > 0 && (
        <details className="rounded-lg border border-l-4 border-l-agent-reply bg-white p-3">
          <summary className="cursor-pointer text-xs uppercase font-bold text-agent-reply select-none">
            Inbound replies · {replies.length}
          </summary>
          <div className="mt-2 space-y-2">
            {replies.map((r) => (
              <div key={r.id} className="text-xs text-sandstone-800 border-t border-sandstone-100 pt-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold">{r.classification}</span>
                  <span
                    className={`text-[10px] uppercase rounded px-1.5 py-0.5 ${
                      r.sentiment === "positive"
                        ? "bg-emerald-100 text-emerald-800"
                        : r.sentiment === "negative"
                        ? "bg-red-100 text-red-800"
                        : "bg-sandstone-100 text-sandstone-700"
                    }`}
                  >
                    {r.sentiment}
                  </span>
                </div>
                <div className="text-[10px] text-sandstone-500 mt-0.5">
                  next action: {r.recommended_next_action} · {fmtTime(r.received_at)}
                </div>
                <pre className="whitespace-pre-wrap font-sans text-[11.5px] text-sandstone-700 mt-1 max-h-40 overflow-y-auto">
                  {r.raw_reply_text}
                </pre>
              </div>
            ))}
          </div>
        </details>
      )}

      {payments.length > 0 && (
        <details open className="rounded-lg border border-l-4 border-l-agent-closer bg-white p-3">
          <summary className="cursor-pointer text-xs uppercase font-bold text-agent-closer select-none">
            Payment events · {payments.length}
          </summary>
          <div className="mt-2 space-y-2">
            {payments.map((p) => (
              <div key={p.id} className="text-xs text-sandstone-800 border-t border-sandstone-100 pt-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold">
                    {p.commercial_event_type} · {p.currency} {Number(p.amount).toLocaleString()}
                  </span>
                  <span
                    className={`text-[10px] uppercase rounded px-1.5 py-0.5 ${
                      p.payment_status === "paid"
                        ? "bg-emerald-100 text-emerald-800"
                        : p.payment_status === "expired" || p.payment_status === "failed"
                        ? "bg-red-100 text-red-800"
                        : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {p.payment_status}
                  </span>
                </div>
                <div className="text-[10px] text-sandstone-500 mt-0.5">
                  ref: {p.doku_reference_id} · expires {fmtTime(p.expires_at)}
                </div>
                <a
                  href={p.payment_link}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[11px] text-terracotta-700 underline break-all"
                >
                  {p.payment_link}
                </a>
                {p.payment_status === "created" && onSimulatePay && (
                  <div className="mt-2 flex gap-1">
                    <button
                      onClick={() => onSimulatePay(p.doku_reference_id, "paid")}
                      className="text-[10px] bg-emerald-600 hover:bg-emerald-700 text-white rounded px-2 py-1"
                    >
                      Mark paid
                    </button>
                    <button
                      onClick={() => onSimulatePay(p.doku_reference_id, "expired")}
                      className="text-[10px] bg-amber-600 hover:bg-amber-700 text-white rounded px-2 py-1"
                    >
                      Mark expired
                    </button>
                    <button
                      onClick={() => onSimulatePay(p.doku_reference_id, "failed")}
                      className="text-[10px] bg-red-600 hover:bg-red-700 text-white rounded px-2 py-1"
                    >
                      Mark failed
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
