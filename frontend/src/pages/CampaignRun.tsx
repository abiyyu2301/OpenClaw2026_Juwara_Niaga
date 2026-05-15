import { useEffect, useRef, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { AgentFeed } from "../components/AgentFeed";
import { DebatePanel } from "../components/DebatePanel";
import { EmailHistory } from "../components/EmailHistory";
import { LeadKanban } from "../components/LeadKanban";
import { api, type Campaign, type Lead, type Run } from "../lib/api";
import { useI18n } from "../lib/i18n";
import { connectRun, type FeedEvent } from "../lib/ws";

export default function CampaignRun() {
  const { t } = useI18n();
  const params = useParams<{ id: string }>();
  const navigate = useNavigate();
  const campaignId = Number(params.id);
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [run, setRun] = useState<Run | null>(null);
  const [events, setEvents] = useState<FeedEvent[]>([]);
  const [activeLead, setActiveLead] = useState<Lead | null>(null);
  const [profile, setProfile] = useState<any>(null);
  const [debate, setDebate] = useState<any>(null);
  const [drafts, setDrafts] = useState<any[]>([]);
  const [replies, setReplies] = useState<any[]>([]);
  const [payments, setPayments] = useState<any[]>([]);
  const [wsOpen, setWsOpen] = useState(false);
  const [findingLeads, setFindingLeads] = useState(false);
  const [findError, setFindError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!campaignId) return;
    api.getCampaign(campaignId).then(setCampaign).catch(() => navigate("/"));
    refreshLeads();
  }, [campaignId, navigate]);

  useEffect(() => {
    if (!run || run.status === "completed") return;
    const timer = setInterval(() => {
      refreshLeads();
      api.getRun(run.id).then(setRun).catch(() => {});
    }, 2500);
    return () => clearInterval(timer);
  }, [run?.id, run?.status]);

  useEffect(() => {
    if (!activeLead) return;
    api.getLead(activeLead.id).then((r: any) => {
      setProfile(r.profile);
      setDebate(r.debate);
      setDrafts(r.drafts || []);
      setReplies(r.replies || []);
      setPayments(r.payments || []);
    });
  }, [activeLead?.id, events.length]);

  async function refreshLeads() {
    if (!campaignId) return;
    try {
      setLeads(await api.listLeads(campaignId));
    } catch {
      // ignore
    }
  }

  async function handleStart() {
    setEvents([]);
    const r = await api.startRun(campaignId);
    setRun(r);
    wsRef.current?.close();
    wsRef.current = connectRun(
      r.id,
      (evt) => {
        setEvents((prev) => {
          const next = [...prev, evt];
          return next.length > 800 ? next.slice(-800) : next;
        });
        if (evt.lead_id) {
          setActiveLead((cur) => cur ?? leads.find((l) => l.id === evt.lead_id) ?? null);
        }
      },
      setWsOpen,
    );
  }

  async function handlePause() {
    if (!run) return;
    await api.pauseRun(run.id);
    setRun(await api.getRun(run.id));
  }

  async function handleResume() {
    if (!run) return;
    await api.resumeRun(run.id);
    setRun(await api.getRun(run.id));
  }

  async function handleStop() {
    if (!run) return;
    await api.stopRun(run.id);
    setRun(await api.getRun(run.id));
    wsRef.current?.close();
  }

  async function handleFindLeads() {
    setFindingLeads(true);
    setFindError(null);
    try {
      await api.findLeads(campaignId, 3);
      await refreshLeads();
    } catch (e: any) {
      setFindError(String(e?.message || e));
    } finally {
      setFindingLeads(false);
    }
  }

  async function handleSimulatePay(ref: string, status: "paid" | "failed" | "expired") {
    await api.simulatePay(ref, status);
    if (activeLead) {
      const r = (await api.getLead(activeLead.id)) as any;
      setPayments(r.payments || []);
      setProfile(r.profile);
    }
    await refreshLeads();
    if (run) setRun(await api.getRun(run.id));
  }

  return (
    <div className="flex-1 overflow-auto px-6 py-6">
      <Link
        to={`/campaigns/${campaignId}`}
        className="text-xs text-stone-500 hover:text-stone-800 mb-3 inline-block"
      >
        {t("back_overview")}
      </Link>

      <div className="flex items-end justify-between mb-4 gap-4">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold text-stone-900 truncate">
            {campaign?.name || "…"}
          </h1>
          <p className="text-xs text-stone-500 mt-1 truncate">
            {campaign?.target_industry} · {campaign?.geography} · {t("card_per_run_prefix")}{" "}
            {campaign?.max_leads_per_run} {t("max_leads_run")}
            {run && (
              <span className="ml-2">
                run #{run.id} ·{" "}
                <span
                  className={
                    run.status === "running"
                      ? "text-emerald-600"
                      : run.status === "paused"
                      ? "text-amber-600"
                      : ""
                  }
                >
                  {run.status}
                </span>
                {!wsOpen && run.status === "running" ? " · ws off" : ""}
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-2 shrink-0">
          <button
            type="button"
            onClick={handleFindLeads}
            disabled={findingLeads}
            className="text-sm px-3 py-2 rounded-lg border border-stone-300 bg-white hover:bg-stone-50 disabled:opacity-50"
          >
            {findingLeads ? t("finding") : `🔎 ${t("find_leads")}`}
          </button>
          {(!run || run.status === "completed") && (
            <button
              type="button"
              onClick={handleStart}
              className="text-sm px-4 py-2 rounded-lg bg-stone-900 text-white font-semibold hover:bg-stone-800"
            >
              ▶ {t("start_run")}
            </button>
          )}
          {run?.status === "running" && (
            <button
              type="button"
              onClick={handlePause}
              className="text-sm px-3 py-2 rounded-lg border border-stone-300 bg-white"
            >
              ⏸ {t("pause")}
            </button>
          )}
          {run?.status === "paused" && (
            <button
              type="button"
              onClick={handleResume}
              className="text-sm px-3 py-2 rounded-lg bg-emerald-600 text-white"
            >
              ▶ {t("resume")}
            </button>
          )}
          {run && run.status !== "completed" && (
            <button
              type="button"
              onClick={handleStop}
              className="text-sm px-3 py-2 rounded-lg border border-stone-300 bg-white"
            >
              ■ {t("stop")}
            </button>
          )}
        </div>
      </div>

      {findError && (
        <div className="mb-3 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm px-3 py-2">
          {findError}
        </div>
      )}

      <div className="grid grid-cols-5 gap-2 mb-4">
        <Kpi label={t("processed")} value={run?.leads_processed ?? 0} />
        <Kpi label={t("qualified")} value={run?.leads_qualified ?? 0} />
        <Kpi label={t("emails_sent")} value={run?.emails_sent ?? 0} />
        <Kpi label={t("deals_closed")} value={run?.deals_closed ?? 0} />
        <Kpi
          label={t("revenue")}
          value={run ? `Rp ${run.total_revenue.toLocaleString("id-ID")}` : "Rp 0"}
          accent
        />
      </div>

      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-5">
          <h2 className="text-[10px] uppercase tracking-wider text-stone-500 mb-2 font-semibold">
            {t("lead_pipeline")}
          </h2>
          <LeadKanban leads={leads} activeLeadId={activeLead?.id} onSelect={setActiveLead} />
        </div>
        <div className="col-span-4">
          <h2 className="text-[10px] uppercase tracking-wider text-stone-500 mb-2 font-semibold">
            {t("agent_feed")}
          </h2>
          <AgentFeed events={events} emptyMessage={t("waiting_agents")} />
        </div>
        <div className="col-span-3 space-y-3">
          <div>
            <h2 className="text-[10px] uppercase tracking-wider text-stone-500 mb-2 font-semibold">
              {t("active_lead")}
            </h2>
            <DebatePanel lead={activeLead} profile={profile} debate={debate} />
          </div>
          {activeLead && (
            <div>
              <h2 className="text-[10px] uppercase tracking-wider text-stone-500 mb-2 font-semibold">
                {t("emails_payments")}
              </h2>
              <EmailHistory
                drafts={drafts}
                replies={replies}
                payments={payments}
                onSimulatePay={handleSimulatePay}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Kpi({
  label,
  value,
  accent,
}: {
  label: string;
  value: number | string;
  accent?: boolean;
}) {
  return (
    <div className="rounded-xl border border-stone-200 bg-white px-3 py-3 shadow-sm">
      <div className="text-[10px] uppercase tracking-wider text-stone-500 font-medium">{label}</div>
      <div
        className={`text-2xl font-bold mt-0.5 ${accent ? "text-orange-600" : "text-stone-900"}`}
      >
        {value}
      </div>
    </div>
  );
}
