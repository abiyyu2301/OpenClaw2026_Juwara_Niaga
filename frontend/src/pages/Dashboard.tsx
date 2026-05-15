import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type CampaignSummary, type DashboardStats } from "../lib/api";
import { useI18n } from "../lib/i18n";

function pct(n: number) {
  return `${Math.round(n * 100)}%`;
}

function formatMoney(n: number, locale: string) {
  if (locale === "en") return `IDR ${n.toLocaleString("en-US")}`;
  return `Rp ${n.toLocaleString("id-ID")}`;
}

export default function Dashboard() {
  const { t, locale } = useI18n();
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    api.getDashboard().then(setStats).catch(() => setStats(null));
  }, []);

  return (
    <div className="flex-1 overflow-auto px-8 py-8">
      <div className="flex items-end justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-stone-900">{t("dashboard_title")}</h1>
          <p className="text-stone-500 mt-1 text-sm">{t("dashboard_sub")}</p>
        </div>
        <Link
          to="/campaigns/new"
          className="bg-stone-900 hover:bg-stone-800 text-white text-sm font-semibold rounded-lg px-4 py-2.5"
        >
          {t("new_campaign")}
        </Link>
      </div>

      {stats && (
        <section className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-8">
          <ManusMetric
            label={t("metric_leads_processed")}
            value={String(stats.leads_processed)}
            sub={t("metric_leads_sub")}
          />
          <ManusMetric
            label={t("metric_qualified")}
            value={String(stats.leads_qualified)}
            sub={`${pct(stats.qualify_rate)} ${t("metric_conversion")}`}
          />
          <ManusMetric
            label={t("metric_emails")}
            value={String(stats.emails_sent)}
            sub={t("metric_emails_sub")}
          />
          <ManusMetric
            label={t("metric_deals")}
            value={String(stats.deals_closed)}
            sub={t("metric_deals_sub")}
          />
          <ManusMetric
            label={t("metric_revenue")}
            value={formatMoney(stats.total_revenue, locale)}
            sub={t("metric_revenue_sub")}
            accent
          />
        </section>
      )}

      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-stone-900">{t("active_campaigns")}</h2>
          <Link to="/campaigns/new" className="text-sm text-stone-600 hover:text-stone-900">
            {t("create_new")}
          </Link>
        </div>

        {!stats?.campaigns.length ? (
          <div className="rounded-xl border border-dashed border-stone-300 bg-white p-12 text-center">
            <p className="text-stone-600 mb-4">{t("no_campaigns")}</p>
            <Link
              to="/campaigns/new"
              className="inline-block bg-stone-900 text-white font-semibold rounded-lg px-4 py-2"
            >
              {t("first_campaign")}
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {stats.campaigns.map((c) => (
              <CampaignCard key={c.id} c={c} locale={locale} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function ManusMetric({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string;
  sub: string;
  accent?: boolean;
}) {
  return (
    <div className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
      <p className="text-[10px] uppercase tracking-wider text-stone-500 font-medium">{label}</p>
      <p
        className={`text-3xl font-bold mt-1 tracking-tight ${
          accent ? "text-orange-600" : "text-stone-900"
        }`}
      >
        {value}
      </p>
      <p className="text-xs text-stone-500 mt-1">{sub}</p>
    </div>
  );
}

function CampaignCard({ c, locale }: { c: CampaignSummary; locale: string }) {
  const { t } = useI18n();
  const active = c.active_run_id != null;
  const total = Math.max(c.leads_total, 1);
  const seg = [
    { w: (c.leads_total / total) * 100, color: "bg-blue-400" },
    { w: (c.leads_qualified / total) * 100, color: "bg-amber-400" },
    { w: (c.emails_sent / total) * 100, color: "bg-cyan-400" },
    { w: (c.deals_closed / total) * 100, color: "bg-orange-500" },
  ];

  return (
    <Link
      to={`/campaigns/${c.id}`}
      className="block rounded-xl border border-stone-200 bg-white p-5 hover:border-stone-400 hover:shadow-md transition-shadow"
    >
      <div className="flex justify-between items-start gap-2">
        <h3 className="font-semibold text-stone-900 truncate">{c.name}</h3>
        <span
          className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${
            active ? "bg-emerald-100 text-emerald-800" : "bg-stone-100 text-stone-600"
          }`}
        >
          {active ? t("status_active") : t("status_ready")}
        </span>
      </div>
      <p className="text-xs text-stone-500 mt-1 truncate">
        {c.target_industry || "—"} · {c.geography || c.geo_place_name || "—"}
      </p>
      {c.offer && (
        <p className="text-xs text-stone-600 mt-2 line-clamp-2">{c.offer}</p>
      )}
      <div className="mt-3 h-1.5 rounded-full overflow-hidden flex bg-stone-100">
        {seg.map((s, i) => (
          <div key={i} className={`h-full ${s.color}`} style={{ width: `${s.w}%` }} />
        ))}
      </div>
      <p className="text-xs text-stone-500 mt-2">
        {c.leads_total} {t("card_leads")} · {c.emails_sent} {t("card_emails")} · {t("card_per_run_prefix")}{" "}
        {c.max_leads_per_run}/{t("card_per_run")}
        {c.total_revenue > 0 ? ` · ${formatMoney(c.total_revenue, locale)}` : ""}
      </p>
    </Link>
  );
}
