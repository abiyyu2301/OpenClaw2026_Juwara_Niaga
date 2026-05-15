import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { AgentFeed } from "../components/AgentFeed";
import { DebatePanel } from "../components/DebatePanel";
import { EmailHistory } from "../components/EmailHistory";
import { LeadKanban } from "../components/LeadKanban";
import { api, type Campaign, type Lead, type Run } from "../lib/api";
import { connectRun, type FeedEvent } from "../lib/ws";

export default function CampaignRun() {
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

  // Load campaign + leads on mount
  useEffect(() => {
    if (!campaignId) return;
    api.getCampaign(campaignId).then(setCampaign).catch(() => navigate("/"));
    refreshLeads();
  }, [campaignId]);

  // Poll leads + active run while a run is active
  useEffect(() => {
    if (!run || run.status === "completed") return;
    const t = setInterval(() => {
      refreshLeads();
      api.getRun(run.id).then(setRun).catch(() => {});
    }, 2500);
    return () => clearInterval(t);
  }, [run?.id, run?.status]);

  // Refresh active lead detail when selected lead changes or events arrive
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
    // Connect WebSocket for live feed
    wsRef.current?.close();
    wsRef.current = connectRun(
      r.id,
      (evt) => {
        setEvents((prev) => {
          const next = [...prev, evt];
          return next.length > 800 ? next.slice(-800) : next;
        });
        // Auto-focus on the lead being processed
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
      const r = await api.getLead(activeLead.id) as any;
      setPayments(r.payments || []);
      setProfile(r.profile);
    }
    await refreshLeads();
    if (run) setRun(await api.getRun(run.id));
  }

  return (
    <div className="mx-auto max-w-[1600px] px-4 py-4">
      {/* Top bar */}
      <div className="flex items-end justify-between mb-3">
        <div>
          <h1 className="font-serif-display text-2xl font-bold text-sandstone-900">
            {campaign?.name || "…"}
          </h1>
          <div className="text-xs text-sandstone-500">
            {campaign?.target_industry} · {campaign?.geography} · max {campaign?.max_leads_per_run} leads/run
            {run && (
              <span className="ml-3">
                run #{run.id} ·{" "}
                <span
                  className={
                    run.status === "running"
                      ? "text-emerald-600"
                      : run.status === "paused"
                      ? "text-amber-600"
                      : "text-sandstone-500"
                  }
                >
                  {run.status}
                </span>
                {wsOpen ? "" : " · ws disconnected"}
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-2 items-center">
          <button
            onClick={handleFindLeads}
            disabled={findingLeads}
            className="bg-sandstone-100 border border-sandstone-300 hover:bg-sandstone-200 text-sandstone-900 font-medium rounded px-3 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Use Gemini with Google Search to discover 3 new Indonesian leads matching this ICP"
          >
            {findingLeads ? "Searching the web…" : "🔎 Find new leads"}
          </button>
          {(!run || run.status === "completed") && (
            <button
              onClick={handleStart}
              className="bg-terracotta-600 hover:bg-terracotta-700 text-white font-semibold rounded px-4 py-2"
            >
              ▶ Start Autonomous Run
            </button>
          )}
          {run?.status === "running" && (
            <button
              onClick={handlePause}
              className="bg-sandstone-200 hover:bg-sandstone-300 text-sandstone-900 rounded px-4 py-2"
            >
              ⏸ Pause
            </button>
          )}
          {run?.status === "paused" && (
            <button
              onClick={handleResume}
              className="bg-emerald-600 hover:bg-emerald-700 text-white rounded px-4 py-2"
            >
              ▶ Resume
            </button>
          )}
          {run && run.status !== "completed" && (
            <button
              onClick={handleStop}
              className="bg-sandstone-200 hover:bg-sandstone-300 text-sandstone-900 rounded px-4 py-2"
            >
              ■ Stop
            </button>
          )}
        </div>
      </div>

      {findError && (
        <div className="mb-3 rounded bg-red-50 border border-red-200 text-red-800 text-sm px-3 py-2">
          Find leads failed: {findError}
        </div>
      )}

      {/* KPI tiles */}
      <div className="grid grid-cols-5 gap-2 mb-3">
        <Tile label="Processed" value={run?.leads_processed ?? 0} />
        <Tile label="Qualified" value={run?.leads_qualified ?? 0} />
        <Tile label="Emails sent" value={run?.emails_sent ?? 0} />
        <Tile label="Deals closed" value={run?.deals_closed ?? 0} accent />
        <Tile
          label="Revenue"
          value={run ? `Rp ${run.total_revenue.toLocaleString()}` : "Rp 0"}
          accent
        />
      </div>

      {/* 3-column layout */}
      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-5">
          <h2 className="text-xs uppercase tracking-wider text-sandstone-500 mb-1">
            Lead pipeline
          </h2>
          <LeadKanban leads={leads} activeLeadId={activeLead?.id} onSelect={setActiveLead} />
        </div>
        <div className="col-span-4">
          <h2 className="text-xs uppercase tracking-wider text-sandstone-500 mb-1">
            Agent feed (live)
          </h2>
          <AgentFeed events={events} />
        </div>
        <div className="col-span-3 space-y-3">
          <div>
            <h2 className="text-xs uppercase tracking-wider text-sandstone-500 mb-1">
              Active lead
            </h2>
            <DebatePanel lead={activeLead} profile={profile} debate={debate} />
          </div>
          {activeLead && (
            <div>
              <h2 className="text-xs uppercase tracking-wider text-sandstone-500 mb-1">
                Emails & payments
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

function Tile({ label, value, accent }: { label: string; value: number | string; accent?: boolean }) {
  return (
    <div className="rounded border border-sandstone-200 bg-white px-3 py-2">
      <div className="text-[10px] uppercase tracking-wider text-sandstone-500">{label}</div>
      <div
        className={`font-serif-display text-2xl font-bold ${
          accent ? "text-terracotta-600" : "text-sandstone-900"
        }`}
      >
        {value}
      </div>
    </div>
  );
}
