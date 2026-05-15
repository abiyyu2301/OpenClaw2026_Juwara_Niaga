import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Campaign, type Run } from "../lib/api";

export default function Dashboard() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [health, setHealth] = useState<string>("?");

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((h) => setHealth(h.status))
      .catch(() => setHealth("down"));
    api.listCampaigns().then(setCampaigns).catch(() => {});
    api.listRuns().then(setRuns).catch(() => {});
  }, []);

  const totals = runs.reduce(
    (acc, r) => ({
      processed: acc.processed + (r.leads_processed || 0),
      qualified: acc.qualified + (r.leads_qualified || 0),
      sent: acc.sent + (r.emails_sent || 0),
      closed: acc.closed + (r.deals_closed || 0),
      revenue: acc.revenue + (r.total_revenue || 0),
    }),
    { processed: 0, qualified: 0, sent: 0, closed: 0, revenue: 0 },
  );

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      <div className="flex items-end justify-between mb-8">
        <div>
          <h1 className="font-serif-display text-4xl font-bold text-sandstone-900">
            Selamat datang, Tim Juwara.
          </h1>
          <p className="text-sandstone-600 mt-1">
            Your autonomous AI sales team. Backend:{" "}
            <span className={health === "ok" ? "text-emerald-700 font-mono-feed" : "text-red-600 font-mono-feed"}>
              {health}
            </span>
          </p>
        </div>
        <Link
          to="/campaigns/new"
          className="bg-terracotta-600 hover:bg-terracotta-700 text-white font-semibold rounded px-4 py-2"
        >
          + New campaign
        </Link>
      </div>

      <div className="grid grid-cols-5 gap-3 mb-8">
        <Tile label="Leads processed" value={totals.processed} />
        <Tile label="Qualified" value={totals.qualified} />
        <Tile label="Emails sent" value={totals.sent} />
        <Tile label="Deals closed" value={totals.closed} accent />
        <Tile
          label="Revenue collected"
          value={`Rp ${totals.revenue.toLocaleString()}`}
          accent
        />
      </div>

      <h2 className="font-serif-display text-2xl text-sandstone-900 mb-3">Campaigns</h2>
      {campaigns.length === 0 ? (
        <div className="rounded-lg border border-dashed border-sandstone-300 bg-white p-8 text-center">
          <p className="text-sandstone-600 mb-3">No campaigns yet.</p>
          <Link
            to="/campaigns/new"
            className="bg-terracotta-600 hover:bg-terracotta-700 text-white font-semibold rounded px-4 py-2 inline-block"
          >
            Create your first campaign
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {campaigns.map((c) => (
            <Link
              key={c.id}
              to={`/campaigns/${c.id}/run`}
              className="block rounded-lg border border-sandstone-200 bg-white p-4 hover:ring-2 hover:ring-terracotta-300"
            >
              <h3 className="font-semibold text-sandstone-900">{c.name}</h3>
              <p className="text-xs text-sandstone-500 mt-1">
                {c.target_industry} · {c.geography} · max {c.max_leads_per_run} leads/run
              </p>
              <p className="text-xs text-sandstone-500 mt-1">{c.offer}</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function Tile({ label, value, accent }: { label: string; value: number | string; accent?: boolean }) {
  return (
    <div className="rounded-lg border border-sandstone-200 bg-white p-4">
      <p className="text-xs uppercase tracking-wider text-sandstone-500">{label}</p>
      <p
        className={`mt-1 text-3xl font-serif-display font-bold ${
          accent ? "text-terracotta-600" : "text-sandstone-900"
        }`}
      >
        {value}
      </p>
    </div>
  );
}
