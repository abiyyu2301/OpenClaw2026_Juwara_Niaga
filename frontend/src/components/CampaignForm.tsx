import { useEffect, useMemo, useState } from "react";
import { ComboField } from "./ComboField";
import { GeoPicker } from "./GeoPicker";
import { MultiSelectChips } from "./MultiSelectChips";
import { NumberInput } from "./NumberInput";
import { CURRENCIES, getCampaignOptions, suggestMaxLeads } from "../lib/campaignOptions";
import { api, type Campaign } from "../lib/api";
import { useI18n, type TranslationKey } from "../lib/i18n";

const STEP_KEYS: TranslationKey[] = [
  "step_0",
  "step_1",
  "step_2",
  "step_3",
  "step_4",
];

export interface CampaignFormProps {
  mode: "create" | "edit";
  initial?: Partial<Campaign>;
  campaignId?: number;
  onDone: (c: Campaign) => void;
  onCancel: () => void;
}

const DEFAULT: Partial<Campaign> = {
  name: "",
  target_industry: "Pelatihan korporat",
  company_size: "11–50 karyawan",
  geography: "Jakarta & Jabodetabek",
  buyer_role: "Founder / Pemilik",
  pain_points: "",
  offer: "",
  pricing_range_min: 500_000,
  pricing_range_max: 2_000_000,
  currency: "IDR",
  disqualifiers: "",
  autonomous_mode: true,
  max_leads_per_run: 10,
  sales_target_revenue: 10_000_000,
  geo_radius_km: 25,
  sales_voice: "",
};

export function CampaignForm({ mode, initial, campaignId, onDone, onCancel }: CampaignFormProps) {
  const { t, locale } = useI18n();
  const opts = getCampaignOptions(locale);
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<Partial<Campaign>>({
    ...DEFAULT,
    sales_voice: DEFAULT.sales_voice || opts.salesVoices[0],
    ...initial,
  });
  const [mapsKey, setMapsKey] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [seedLeads, setSeedLeads] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);

  useEffect(() => {
    api.getPublicConfig().then((c) => setMapsKey(c.maps_api_key));
  }, []);

  function set<K extends keyof Campaign>(key: K, value: Campaign[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  const suggested = useMemo(
    () =>
      suggestMaxLeads(
        form.sales_target_revenue || 0,
        form.pricing_range_min || 0,
        form.pricing_range_max || 0,
      ),
    [form.sales_target_revenue, form.pricing_range_min, form.pricing_range_max],
  );

  async function handleUpload(file: File) {
    if (!campaignId) {
      setUploadMsg(t("upload_save_first"));
      return;
    }
    setUploading(true);
    setUploadMsg(null);
    try {
      const asset = await api.uploadAsset(campaignId, file);
      set("promo_asset_url", asset.storage_url);
      set("promo_asset_type", asset.asset_type as any);
      setUploadMsg(t("upload_ok"));
    } catch (e: any) {
      setUploadMsg(String(e?.message || e));
    } finally {
      setUploading(false);
    }
  }

  function normalizedPayload(): Partial<Campaign> {
    let industry = form.target_industry || "";
    if (industry === opts.otherLabel || industry === "Lainnya" || industry === "Other") {
      industry = "";
    }
    return {
      ...form,
      target_industry: industry,
      max_leads_per_run: form.max_leads_per_run || suggested,
    };
  }

  async function submit() {
    setBusy(true);
    setErr(null);
    const payload = normalizedPayload();
    try {
      let c: Campaign;
      if (mode === "edit" && campaignId) {
        c = await api.updateCampaign(campaignId, payload);
      } else {
        c = await api.createCampaign(payload);
        if (seedLeads) {
          const seeds = [
            {
              company_name: "PT Mitra Edukasi Nusantara",
              industry: "Pelatihan korporat",
              buyer_name: "Ibu Sri Wahyuni",
              buyer_role: "Direktur Operasional",
              email: "sri@mitraedukasi.example.id",
              raw_notes: "Provider pelatihan B2B Jakarta, sedang rekrut admin sales.",
            },
            {
              company_name: "PT Karya Sukses Bersama",
              industry: "Network marketing / MLM",
              buyer_name: "Pak Hendra",
              buyer_role: "Founder",
              email: "hendra@karyasukses.example.id",
              raw_notes: "MLM — contoh lead yang seharusnya diskualifikasi.",
            },
            {
              company_name: "Belajar Pintar Indonesia",
              industry: "EdTech / L&D",
              buyer_name: "Ibu Ratna",
              buyer_role: "Head of Partnerships",
              email: "ratna@belajarpintar.example.id",
              raw_notes: "EdTech hybrid — lead ambigu untuk demo debate.",
            },
          ];
          for (const lead of seeds) {
            await api.createLead({ ...lead, campaign_id: c.id });
          }
        }
      }
      onDone(c);
    } catch (e: any) {
      setErr(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      <h1 className="text-2xl font-bold text-sandstone-900 mb-1">
        {mode === "create" ? t("campaign_new") : t("campaign_edit")}
      </h1>
      <p className="text-sm text-sandstone-600 mb-6">{t("campaign_intro")}</p>

      <ol className="flex gap-1 mb-6 overflow-x-auto pb-1">
        {STEP_KEYS.map((key, i) => (
          <li
            key={key}
            className={`text-xs px-2 py-1 rounded whitespace-nowrap ${
              i === step
                ? "bg-terracotta-600 text-white"
                : i < step
                ? "bg-terracotta-100 text-terracotta-800"
                : "bg-sandstone-100 text-sandstone-600"
            }`}
          >
            {i + 1}. {t(key)}
          </li>
        ))}
      </ol>

      <div className="bg-white rounded-xl border border-sandstone-200 p-6 space-y-4">
        {step === 0 && (
          <>
            <Field label={t("field_campaign_name")} hint={t("hint_campaign_name")}>
              <input
                className="input"
                placeholder={t("ph_campaign_name")}
                value={form.name || ""}
                onChange={(e) => set("name", e.target.value)}
                required
              />
            </Field>
            <Field label={t("field_revenue_target")} hint={t("hint_revenue_target")}>
              <NumberInput
                value={form.sales_target_revenue}
                onChange={(n) => set("sales_target_revenue", n)}
                placeholder="10.000.000"
              />
            </Field>
            <div className="grid grid-cols-3 gap-3">
              <Field label={t("field_currency")}>
                <select
                  className="input"
                  value={form.currency || "IDR"}
                  onChange={(e) => set("currency", e.target.value)}
                >
                  {CURRENCIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label={t("field_price_min")} hint={t("hint_not_platform")}>
                <NumberInput
                  value={form.pricing_range_min}
                  onChange={(n) => set("pricing_range_min", n)}
                  placeholder="500.000"
                />
              </Field>
              <Field label={t("field_price_max")}>
                <NumberInput
                  value={form.pricing_range_max}
                  onChange={(n) => set("pricing_range_max", n)}
                  placeholder="2.000.000"
                />
              </Field>
            </div>
            <div className="rounded-lg bg-sandstone-50 border border-sandstone-200 p-3 text-sm">
              <p className="text-sandstone-800">
                {t("suggest_leads")} <strong>{suggested}</strong> {t("suggest_leads_note")}
              </p>
              <Field label={t("field_max_leads")}>
                <NumberInput
                  className="input mt-1"
                  value={form.max_leads_per_run ?? suggested}
                  onChange={(n) => set("max_leads_per_run", n)}
                  placeholder={String(suggested)}
                />
              </Field>
            </div>
          </>
        )}

        {step === 1 && (
          <>
            <p className="text-sm font-medium text-sandstone-800">{t("icp_who")}</p>
            <ComboField
              label={t("field_industry")}
              options={opts.industries}
              otherLabel={opts.otherLabel}
              value={form.target_industry || ""}
              onChange={(v) => set("target_industry", v)}
              placeholder={t("ph_industry")}
            />
            <MultiSelectChips
              label={t("field_company_size")}
              hint={t("hint_multi_size")}
              options={opts.companySizes}
              value={form.company_size || ""}
              onChange={(v) => set("company_size", v)}
            />
            <ComboField
              label={t("field_buyer_role")}
              hint={t("hint_buyer_role")}
              options={opts.buyerRoles}
              otherLabel={opts.otherLabel}
              value={form.buyer_role || ""}
              onChange={(v) => set("buyer_role", v)}
            />
            <GeoPicker
              mapsKey={mapsKey}
              placeName={form.geo_place_name || ""}
              radiusKm={form.geo_radius_km || 25}
              manualGeography={form.geography || ""}
              onPlace={(p) => {
                set("geo_place_name", p.placeName);
                set("geo_lat", p.lat);
                set("geo_lng", p.lng);
              }}
              onRadius={(km) => set("geo_radius_km", km)}
              onManual={(text) => set("geography", text)}
            />
            <Field label={t("field_pain")} hint={t("hint_pain")}>
              <textarea
                className="input"
                rows={3}
                placeholder={t("ph_pain")}
                value={form.pain_points || ""}
                onChange={(e) => set("pain_points", e.target.value)}
              />
            </Field>
            <Field label={t("field_disqualifiers")}>
              <textarea
                className="input"
                rows={2}
                placeholder={t("ph_disqualifiers")}
                value={form.disqualifiers || ""}
                onChange={(e) => set("disqualifiers", e.target.value)}
              />
            </Field>
          </>
        )}

        {step === 2 && (
          <>
            <Field label={t("field_offer")} hint={t("hint_offer")}>
              <textarea
                className="input"
                rows={3}
                placeholder={t("ph_offer")}
                value={form.offer || ""}
                onChange={(e) => set("offer", e.target.value)}
              />
            </Field>
            <Field label={t("field_promo")} hint={t("hint_promo")}>
              <input
                type="file"
                accept="image/*,video/mp4,video/webm"
                disabled={uploading}
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleUpload(f);
                }}
              />
              {uploadMsg && <p className="text-xs mt-1 text-sandstone-600">{uploadMsg}</p>}
              {form.promo_asset_url && (
                <p className="text-xs mt-1 text-emerald-700 truncate">{form.promo_asset_url}</p>
              )}
            </Field>
          </>
        )}

        {step === 3 && (
          <>
            <Field label={t("field_rep_name")}>
              <input
                className="input"
                placeholder={t("ph_rep_name")}
                value={form.rep_name || ""}
                onChange={(e) => set("rep_name", e.target.value)}
              />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label={t("field_rep_title")}>
                <input
                  className="input"
                  placeholder={t("ph_rep_title")}
                  value={form.rep_title || ""}
                  onChange={(e) => set("rep_title", e.target.value)}
                />
              </Field>
              <Field label={t("field_rep_email")}>
                <input
                  className="input"
                  placeholder={t("ph_rep_email")}
                  value={form.rep_email || ""}
                  onChange={(e) => set("rep_email", e.target.value)}
                />
              </Field>
            </div>
            <Field label={t("field_rep_phone")}>
              <input
                className="input"
                placeholder={t("ph_rep_phone")}
                value={form.rep_phone || ""}
                onChange={(e) => set("rep_phone", e.target.value)}
              />
            </Field>
            <Field label={t("field_sales_voice")}>
              <select
                className="input"
                value={form.sales_voice || opts.salesVoices[0]}
                onChange={(e) => set("sales_voice", e.target.value)}
              >
                {opts.salesVoices.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </Field>
            <Field label={t("field_voice_samples")} hint={t("hint_voice_samples")}>
              <textarea
                className="input"
                rows={4}
                placeholder={t("ph_voice_samples")}
                value={form.sales_voice_samples || ""}
                onChange={(e) => set("sales_voice_samples", e.target.value)}
              />
            </Field>
          </>
        )}

        {step === 4 && (
          <>
            <label className="flex items-start gap-3 p-3 rounded-lg border border-sandstone-200">
              <input
                type="checkbox"
                className="mt-1"
                checked={form.autonomous_mode ?? true}
                onChange={(e) => set("autonomous_mode", e.target.checked)}
              />
              <span className="text-sm text-sandstone-800">
                <strong>{t("autonomous_label")}</strong> — {t("autonomous_hint")}
              </span>
            </label>
            {mode === "create" && (
              <label className="flex items-start gap-3 p-3 rounded-lg border border-sandstone-200">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={seedLeads}
                  onChange={(e) => setSeedLeads(e.target.checked)}
                />
                <span className="text-sm text-sandstone-800">
                  <strong>{t("demo_leads_label")}</strong>
                  <br />
                  <span className="text-xs text-stone-500">{t("demo_leads_hint")}</span>
                </span>
              </label>
            )}
          </>
        )}
      </div>

      {err && <p className="text-red-600 text-sm mt-3">{err}</p>}

      <div className="mt-5 flex justify-between">
        <button
          type="button"
          onClick={step === 0 ? onCancel : () => setStep((s) => s - 1)}
          className="px-4 py-2 rounded border border-sandstone-300 text-sandstone-700"
        >
          {step === 0 ? t("cancel") : t("back")}
        </button>
        {step < STEP_KEYS.length - 1 ? (
          <button
            type="button"
            onClick={() => setStep((s) => s + 1)}
            className="px-5 py-2 rounded bg-terracotta-600 text-white font-semibold"
          >
            {t("continue")}
          </button>
        ) : (
          <button
            type="button"
            disabled={busy || !form.name}
            onClick={submit}
            className="px-5 py-2 rounded bg-terracotta-600 text-white font-semibold disabled:opacity-50"
          >
            {busy ? t("saving") : mode === "create" ? t("create_campaign") : t("save_changes")}
          </button>
        )}
      </div>
    </div>
  );
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="block text-sm font-medium text-sandstone-800 mb-0.5">{label}</span>
      {hint && <p className="text-xs text-sandstone-500 mb-1">{hint}</p>}
      {children}
    </label>
  );
}
