import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { LeadImportPanel } from "../components/LeadImportPanel";
import { api, type Campaign, type Lead } from "../lib/api";
import { useI18n } from "../lib/i18n";

export default function CampaignOverview() {
  const { t, locale } = useI18n();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const campaignId = Number(id);
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [finding, setFinding] = useState(false);
  const [editingEmail, setEditingEmail] = useState<number | null>(null);
  const [emailDraft, setEmailDraft] = useState("");

  const refreshLeads = useCallback(() => {
    if (!campaignId) return;
    api.listLeads(campaignId).then(setLeads).catch(() => {});
  }, [campaignId]);

  useEffect(() => {
    if (!campaignId) return;
    api.getCampaign(campaignId).then(setCampaign).catch(() => navigate("/"));
    refreshLeads();
  }, [campaignId, navigate, refreshLeads]);

  async function handleFind() {
    setFinding(true);
    try {
      await api.findLeads(campaignId, 3);
      refreshLeads();
    } finally {
      setFinding(false);
    }
  }

  async function saveEmail(leadId: number) {
    try {
      await api.updateLead(leadId, { email: emailDraft.trim() });
      setEditingEmail(null);
      refreshLeads();
    } catch {
      // ignore
    }
  }

  if (!campaign) {
    return <p className="p-10 text-center text-stone-600">{t("loading")}</p>;
  }

  const money =
    locale === "en"
      ? (n: number) => `IDR ${n.toLocaleString("en-US")}`
      : (n: number) => `Rp ${n.toLocaleString("id-ID")}`;

  const byStatus = leads.reduce<Record<string, number>>((acc, l) => {
    acc[l.status] = (acc[l.status] || 0) + 1;
    return acc;
  }, {});
  const withEmail = leads.filter((l) => l.email).length;

  return (
    <div className="flex-1 overflow-auto px-8 py-8 max-w-4xl">
      <nav className="text-xs text-stone-500 mb-4">
        <Link to="/" className="hover:text-orange-600">
          {t("dash_breadcrumb")}
        </Link>
        <span className="mx-2">/</span>
        <span className="text-stone-800">{campaign.name}</span>
      </nav>

      <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-stone-900">{campaign.name}</h1>
          <p className="text-sm text-stone-600 mt-1">
            {campaign.target_industry} · {campaign.geography || campaign.geo_place_name}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            to={`/campaigns/${campaignId}/edit`}
            className="px-3 py-2 text-sm rounded-lg border border-stone-300"
          >
            {t("overview_edit")}
          </Link>
          <Link
            to={`/campaigns/${campaignId}/run`}
            className="px-3 py-2 text-sm rounded-lg bg-stone-900 text-white font-semibold"
          >
            {t("overview_run")}
          </Link>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4 mb-6">
        <InfoCard title={t("overview_revenue")}>
          {campaign.sales_target_revenue
            ? money(campaign.sales_target_revenue)
            : t("not_set")}
        </InfoCard>
        <InfoCard title={t("overview_offer")}>
          <p className="text-sm line-clamp-4">{campaign.offer || "—"}</p>
        </InfoCard>
      </div>

      <LeadImportPanel campaignId={campaignId} onChanged={refreshLeads} />

      <section className="bg-white rounded-xl border border-stone-200 p-5 mt-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="font-semibold text-stone-900">
              {t("prospects_title")} ({leads.length})
            </h2>
            <p className="text-xs text-stone-500">
              {withEmail} {t("prospects_of")} {leads.length} {t("prospects_email_hint")}
            </p>
          </div>
          <button
            type="button"
            onClick={handleFind}
            disabled={finding}
            className="text-sm px-3 py-1.5 rounded-lg bg-stone-100 border border-stone-300 disabled:opacity-50"
          >
            {finding ? t("finding") : t("find_leads_ai")}
          </button>
        </div>
        <div className="flex flex-wrap gap-2 mb-4 text-xs">
          {Object.entries(byStatus).map(([s, n]) => (
            <span key={s} className="px-2 py-1 rounded bg-stone-100">
              {s}: {n}
            </span>
          ))}
        </div>
        <ul className="divide-y divide-stone-100 text-sm">
          {leads.map((l) => (
            <li key={l.id} className="py-3 flex flex-col sm:flex-row sm:items-center gap-2">
              <div className="flex-1 min-w-0">
                <p className="font-medium text-stone-900 truncate">{l.company_name}</p>
                {editingEmail === l.id ? (
                  <div className="flex gap-2 mt-1">
                    <input
                      className="input text-xs py-1"
                      value={emailDraft}
                      onChange={(e) => setEmailDraft(e.target.value)}
                      placeholder={t("ph_lead_email")}
                    />
                    <button
                      type="button"
                      className="text-xs text-stone-700 underline"
                      onClick={() => saveEmail(l.id)}
                    >
                      {t("save")}
                    </button>
                    <button
                      type="button"
                      className="text-xs text-stone-500"
                      onClick={() => setEditingEmail(null)}
                    >
                      {t("cancel")}
                    </button>
                  </div>
                ) : (
                  <p className="text-xs text-stone-500 truncate">
                    {l.email ? (
                      l.email
                    ) : (
                      <button
                        type="button"
                        className="text-orange-600 underline"
                        onClick={() => {
                          setEditingEmail(l.id);
                          setEmailDraft("");
                        }}
                      >
                        {t("add_email")}
                      </button>
                    )}
                    {l.email && (
                      <button
                        type="button"
                        className="ml-2 text-stone-400 hover:text-stone-700"
                        onClick={() => {
                          setEditingEmail(l.id);
                          setEmailDraft(l.email || "");
                        }}
                      >
                        {t("edit_btn")}
                      </button>
                    )}
                  </p>
                )}
              </div>
              <span className="text-xs px-2 py-0.5 rounded-full bg-stone-100 text-stone-600 shrink-0">
                {l.status}
              </span>
            </li>
          ))}
          {leads.length === 0 && (
            <li className="py-4 text-stone-500 text-center">
              {t("no_leads")}
            </li>
          )}
        </ul>
      </section>
    </div>
  );
}

function InfoCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-stone-200 p-4">
      <h3 className="text-xs font-semibold text-stone-500 uppercase tracking-wide mb-2">
        {title}
      </h3>
      <div className="text-sm text-stone-800">{children}</div>
    </div>
  );
}
