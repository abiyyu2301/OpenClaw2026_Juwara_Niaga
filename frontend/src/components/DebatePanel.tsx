import type { Lead } from "../lib/api";

interface DebatePanelProps {
  lead?: Lead | null;
  profile?: any;
  debate?: any;
}

function parseJson(s?: string): any {
  if (!s) return null;
  try {
    return JSON.parse(s);
  } catch {
    return null;
  }
}

export function DebatePanel({ lead, profile, debate }: DebatePanelProps) {
  if (!lead) {
    return (
      <div className="rounded-lg border border-sandstone-200 bg-white p-4 text-sm text-sandstone-500">
        Select a lead from the kanban to see its profile, debate, and verdict.
      </div>
    );
  }

  const bull = parseJson(debate?.bull_argument_json);
  const bear = parseJson(debate?.bear_argument_json);

  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-sandstone-200 bg-white p-4">
        <h3 className="font-serif-display text-lg font-bold text-sandstone-900">
          {lead.company_name}
        </h3>
        <div className="text-xs text-sandstone-500">
          {lead.industry} · {lead.buyer_name} · {lead.buyer_role}
        </div>
        {profile && (
          <div className="mt-3 text-sm">
            <p className="text-sandstone-700">
              <strong>Why relevant:</strong> {profile.why_relevant}
            </p>
            <p className="text-sandstone-700 mt-1">
              <strong>Trigger:</strong> {profile.detected_trigger}
            </p>
            <p className="text-sandstone-700 mt-1">
              <strong>Fit score:</strong> {profile.fit_score}/100 ({profile.confidence_level})
            </p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-lg border-l-4 border-l-agent-bull bg-white p-3">
          <div className="text-xs uppercase font-bold text-agent-bull mb-1">Bull (pursue)</div>
          {bull ? (
            <>
              <ul className="text-xs text-sandstone-800 space-y-1 list-disc list-inside">
                {(bull.top_reasons || []).map((r: string, i: number) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
              <div className="text-[11px] text-sandstone-500 mt-2">
                Rp {Number(bull.estimated_deal_value_idr || 0).toLocaleString()} ·
                close prob {Math.round((bull.estimated_close_probability || 0) * 100)}%
              </div>
            </>
          ) : (
            <div className="text-xs text-sandstone-400">No debate yet.</div>
          )}
        </div>
        <div className="rounded-lg border-l-4 border-l-agent-bear bg-white p-3">
          <div className="text-xs uppercase font-bold text-agent-bear mb-1">Bear (skip)</div>
          {bear ? (
            <>
              <ul className="text-xs text-sandstone-800 space-y-1 list-disc list-inside">
                {(bear.top_objections || []).map((r: string, i: number) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
              <div className="text-[11px] text-sandstone-500 mt-2">
                ~{bear.estimated_time_waste_hours || "?"}h waste · disqualify prob{" "}
                {Math.round((bear.estimated_disqualifier_probability || 0) * 100)}%
              </div>
            </>
          ) : (
            <div className="text-xs text-sandstone-400">No debate yet.</div>
          )}
        </div>
      </div>

      {debate && (
        <div className="rounded-lg border border-l-4 border-l-agent-judge bg-white p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase font-bold text-agent-judge">Judge verdict</span>
            <span
              className={`text-xs font-bold px-2 py-0.5 rounded ${
                debate.verdict === "qualified"
                  ? "bg-emerald-100 text-emerald-800"
                  : "bg-red-100 text-red-800"
              }`}
            >
              {debate.verdict?.toUpperCase()} · fit {debate.fit_score}
            </span>
          </div>
          <p className="text-sm text-sandstone-800 mt-2">{debate.reasoning}</p>
          {debate.recommended_angle && (
            <p className="text-xs text-sandstone-600 mt-2 italic">
              Angle: {debate.recommended_angle}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
