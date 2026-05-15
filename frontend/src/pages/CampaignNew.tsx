import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type Campaign } from "../lib/api";

const DEFAULT: Partial<Campaign> = {
  name: "Niaga pilot — Jakarta corporate training providers",
  target_industry: "corporate training providers",
  company_size: "10-100 karyawan",
  geography: "Jakarta and Jabodetabek",
  buyer_role: "Founder / Director of Operations",
  pain_points: "Manual sales cycle, low conversion, no Bahasa Indonesia outreach automation.",
  offer: "Niaga pilot at Rp 3,000,000/month for 1 month, refundable if we don't close 1 deal in 4 weeks.",
  pricing_range_min: 500_000,
  pricing_range_max: 2_000_000,
  currency: "IDR",
  disqualifiers: "Government agencies, banks, MLM/network marketing companies.",
  autonomous_mode: true,
  max_leads_per_run: 3,
};

interface SeedLead {
  company_name: string;
  industry?: string;
  buyer_name?: string;
  buyer_role?: string;
  email?: string;
  raw_notes?: string;
}

const SEED_LEADS: SeedLead[] = [
  {
    company_name: "PT Mitra Edukasi Nusantara",
    industry: "Corporate training",
    buyer_name: "Ibu Sri Wahyuni",
    buyer_role: "Direktur Operasional",
    email: "sri@mitraedukasi.example.id",
    raw_notes:
      "Mid-size B2B training provider in Jakarta. Runs ~12 leadership workshops/month. " +
      "Recently posted a job opening for a sales admin. Expanding to Bandung. " +
      "Currently relies on referrals and Instagram DMs for new clients.",
  },
  {
    company_name: "PT Karya Sukses Bersama",
    industry: "Network marketing / MLM",
    buyer_name: "Pak Hendra",
    buyer_role: "Founder",
    email: "hendra@karyasukses.example.id",
    raw_notes:
      "MLM company selling health supplements via downline structure. Strong on " +
      "Facebook groups. Looking for 'sales automation' but model is fundamentally " +
      "consumer downline, not B2B corporate training.",
  },
  {
    company_name: "Belajar Pintar Indonesia",
    industry: "EdTech / Corporate L&D",
    buyer_name: "Ibu Ratna",
    buyer_role: "Head of Partnerships",
    email: "ratna@belajarpintar.example.id",
    raw_notes:
      "Hybrid edtech: sells corporate L&D subscriptions to mid-market Jakarta " +
      "companies plus a consumer course platform. ~40 employees. Recently hired " +
      "VP Sales from a SaaS company — might already be building their own outreach " +
      "automation in-house. Strong interest in AI but unclear budget.",
  },
];

export default function CampaignNew() {
  const navigate = useNavigate();
  const [form, setForm] = useState<Partial<Campaign>>(DEFAULT);
  const [seedLeads, setSeedLeads] = useState(true);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  function set<K extends keyof Campaign>(key: K, value: any) {
    setForm({ ...form, [key]: value });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      const c = await api.createCampaign(form);
      if (seedLeads) {
        for (const lead of SEED_LEADS) {
          await api.createLead({ ...lead, campaign_id: c.id });
        }
      }
      navigate(`/campaigns/${c.id}/run`);
    } catch (e: any) {
      setErr(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="font-serif-display text-3xl font-bold text-sandstone-900 mb-1">
        New campaign
      </h1>
      <p className="text-sandstone-600 text-sm mb-6">
        Define your ICP and offer once. Niaga will prospect, debate, qualify, and close
        autonomously.
      </p>

      <div className="space-y-4 bg-white rounded-lg border border-sandstone-200 p-6">
        <Field label="Campaign name">
          <input
            className="input"
            value={form.name || ""}
            onChange={(e) => set("name", e.target.value)}
            required
          />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Target industry">
            <input
              className="input"
              value={form.target_industry || ""}
              onChange={(e) => set("target_industry", e.target.value)}
            />
          </Field>
          <Field label="Company size">
            <input
              className="input"
              value={form.company_size || ""}
              onChange={(e) => set("company_size", e.target.value)}
            />
          </Field>
          <Field label="Geography">
            <input
              className="input"
              value={form.geography || ""}
              onChange={(e) => set("geography", e.target.value)}
            />
          </Field>
          <Field label="Buyer role">
            <input
              className="input"
              value={form.buyer_role || ""}
              onChange={(e) => set("buyer_role", e.target.value)}
            />
          </Field>
        </div>
        <Field label="Pain points">
          <textarea
            className="input"
            rows={2}
            value={form.pain_points || ""}
            onChange={(e) => set("pain_points", e.target.value)}
          />
        </Field>
        <Field label="Offer">
          <textarea
            className="input"
            rows={2}
            value={form.offer || ""}
            onChange={(e) => set("offer", e.target.value)}
          />
        </Field>
        <div className="grid grid-cols-3 gap-3">
          <Field label="Pricing min (IDR)">
            <input
              type="number"
              className="input"
              value={form.pricing_range_min || 0}
              onChange={(e) => set("pricing_range_min", Number(e.target.value))}
            />
          </Field>
          <Field label="Pricing max (IDR)">
            <input
              type="number"
              className="input"
              value={form.pricing_range_max || 0}
              onChange={(e) => set("pricing_range_max", Number(e.target.value))}
            />
          </Field>
          <Field label="Max leads / run">
            <input
              type="number"
              className="input"
              value={form.max_leads_per_run || 3}
              onChange={(e) => set("max_leads_per_run", Number(e.target.value))}
            />
          </Field>
        </div>
        <Field label="Disqualifiers">
          <textarea
            className="input"
            rows={2}
            value={form.disqualifiers || ""}
            onChange={(e) => set("disqualifiers", e.target.value)}
          />
        </Field>

        <label className="flex items-center gap-2 pt-2">
          <input
            type="checkbox"
            checked={form.autonomous_mode ?? true}
            onChange={(e) => set("autonomous_mode", e.target.checked)}
          />
          <span className="text-sm text-sandstone-700">
            Autonomous mode (no human approval between agent steps)
          </span>
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={seedLeads}
            onChange={(e) => setSeedLeads(e.target.checked)}
          />
          <span className="text-sm text-sandstone-700">
            Seed with 3 demo leads (strong fit · weak fit · ambiguous)
          </span>
        </label>
      </div>

      {err && <p className="text-red-600 mt-3 text-sm">{err}</p>}

      <div className="mt-5 flex justify-end gap-2">
        <button
          type="button"
          onClick={() => navigate("/")}
          className="px-4 py-2 rounded border border-sandstone-300 text-sandstone-700 hover:bg-sandstone-100"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={busy}
          className="px-5 py-2 rounded bg-terracotta-600 hover:bg-terracotta-700 text-white font-semibold disabled:opacity-50"
        >
          {busy ? "Creating…" : "Create campaign"}
        </button>
      </div>
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-xs uppercase tracking-wider text-sandstone-500 mb-1">
        {label}
      </span>
      {children}
    </label>
  );
}
