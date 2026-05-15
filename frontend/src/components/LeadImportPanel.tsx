import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useI18n } from "../lib/i18n";
import { parseBulkLeadLines } from "../lib/parseBulkLeads";

interface LeadImportPanelProps {
  campaignId: number;
  onChanged: () => void;
}

export function LeadImportPanel({ campaignId, onChanged }: LeadImportPanelProps) {
  const { t } = useI18n();
  const [emailStatus, setEmailStatus] = useState<{
    configured: boolean;
    dry_run: boolean;
    from_address?: string;
    message: string;
  } | null>(null);
  const [testTo, setTestTo] = useState("");
  const [testMsg, setTestMsg] = useState<string | null>(null);
  const [bulkText, setBulkText] = useState("");
  const [single, setSingle] = useState({ company_name: "", email: "", buyer_name: "" });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  useEffect(() => {
    api.getEmailStatus().then(setEmailStatus).catch(() => {});
  }, []);

  async function handleTestEmail() {
    setBusy(true);
    setTestMsg(null);
    setErr(null);
    try {
      const r = await api.sendTestEmail(testTo);
      setTestMsg(
        r.dry_run ? t("test_dry_run") : t("test_sent", { email: testTo }),
      );
    } catch (e: any) {
      setErr(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }

  async function handleAddOne(e: React.FormEvent) {
    e.preventDefault();
    if (!single.company_name.trim()) return;
    setBusy(true);
    setErr(null);
    setOk(null);
    try {
      await api.createLead({
        campaign_id: campaignId,
        company_name: single.company_name.trim(),
        email: single.email.trim() || undefined,
        buyer_name: single.buyer_name.trim() || undefined,
        raw_notes: "Manual lead for outreach testing.",
      });
      setSingle({ company_name: "", email: "", buyer_name: "" });
      setOk(t("lead_added"));
      onChanged();
    } catch (e: any) {
      setErr(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }

  async function handleBulkImport() {
    const rows = parseBulkLeadLines(bulkText);
    if (!rows.length) {
      setErr(t("bulk_invalid"));
      return;
    }
    setBusy(true);
    setErr(null);
    setOk(null);
    try {
      const created = await api.createLeadsBulk({
        campaign_id: campaignId,
        leads: rows.map((r) => ({
          company_name: r.company_name,
          email: r.email,
          buyer_name: r.buyer_name,
        })),
      });
      setBulkText("");
      setOk(t("import_count", { n: created.length }));
      onChanged();
    } catch (e: any) {
      setErr(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }

  async function handleCsv(file: File) {
    setBusy(true);
    setErr(null);
    try {
      const created = await api.importLeadsCsv(campaignId, file);
      setOk(t("import_csv", { n: created.length }));
      onChanged();
    } catch (e: any) {
      setErr(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }

  const previewCount = parseBulkLeadLines(bulkText).length;

  return (
    <section className="bg-white rounded-xl border border-stone-200 p-5 space-y-5">
      <div>
        <h2 className="font-semibold text-stone-900">{t("prospects_email_section")}</h2>
        <p className="text-xs text-stone-500 mt-1">{t("prospects_email_sub")}</p>
      </div>

      <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-xs text-blue-900">
        <p className="font-semibold mb-1">{t("email_how_title")}</p>
        <p>{t("email_how_body")}</p>
        {emailStatus?.from_address && (
          <p className="mt-2">
            {t("smtp_label")}{" "}
            <code className="bg-blue-100 px-1">{emailStatus.from_address}</code>
          </p>
        )}
      </div>

      {emailStatus && (
        <div
          className={`text-sm rounded-lg p-3 border ${
            emailStatus.configured
              ? "bg-emerald-50 border-emerald-200 text-emerald-900"
              : "bg-amber-50 border-amber-200 text-amber-900"
          }`}
        >
          <p className="font-medium">
            {emailStatus.configured ? t("email_active") : t("email_sim")}
          </p>
        </div>
      )}

      <div className="rounded-lg border border-stone-200 p-4">
        <p className="text-sm font-medium text-stone-800 mb-2">{t("test_email")}</p>
        <p className="text-xs text-stone-500 mb-3">{t("test_email_hint")}</p>
        <div className="flex gap-2 flex-wrap">
          <input
            className="input flex-1 min-w-[200px]"
            placeholder={t("ph_test_email")}
            value={testTo}
            onChange={(e) => setTestTo(e.target.value)}
          />
          <button
            type="button"
            disabled={busy || !testTo}
            onClick={handleTestEmail}
            className="px-4 py-2 rounded-lg bg-stone-900 text-white text-sm disabled:opacity-50"
          >
            {t("send_test")}
          </button>
        </div>
        {testMsg && <p className="text-xs text-emerald-700 mt-2">{testMsg}</p>}
      </div>

      <form onSubmit={handleAddOne} className="rounded-lg border border-stone-200 p-4 space-y-3">
        <p className="text-sm font-medium text-stone-800">{t("add_lead")}</p>
        <input
          className="input"
          placeholder={t("ph_company_required")}
          value={single.company_name}
          onChange={(e) => setSingle({ ...single, company_name: e.target.value })}
          required
        />
        <input
          className="input"
          type="email"
          placeholder={t("prospect_email")}
          value={single.email}
          onChange={(e) => setSingle({ ...single, email: e.target.value })}
        />
        <input
          className="input"
          placeholder={t("buyer_name")}
          value={single.buyer_name}
          onChange={(e) => setSingle({ ...single, buyer_name: e.target.value })}
        />
        <button
          type="submit"
          disabled={busy}
          className="text-sm px-4 py-2 rounded-lg border border-stone-300 hover:bg-stone-50 disabled:opacity-50"
        >
          {t("save_lead")}
        </button>
      </form>

      <div className="rounded-lg border border-stone-200 p-4 space-y-3">
        <p className="text-sm font-medium text-stone-800">{t("bulk_import")}</p>
        <p className="text-xs text-stone-500">
          {t("bulk_format")}{" "}
          <code className="bg-stone-100 px-1">PT ABC, email@pt.com</code>
        </p>
        <textarea
          className="input font-mono text-xs"
          rows={6}
          placeholder={`PT Mitra Edu, kontak@mitra.co.id\nhalo@startup.id`}
          value={bulkText}
          onChange={(e) => setBulkText(e.target.value)}
        />
        <button
          type="button"
          disabled={busy || !bulkText.trim()}
          onClick={handleBulkImport}
          className="text-sm px-4 py-2 rounded-lg bg-stone-900 text-white disabled:opacity-50"
        >
          {t("import_leads")}
          {previewCount ? ` (${previewCount})` : ""}
        </button>
      </div>

      <p className="text-xs text-stone-500">
        <label className="cursor-pointer underline hover:text-stone-800">
          {t("upload_csv")}
          <input
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleCsv(f);
            }}
          />
        </label>{" "}
        — {t("csv_columns")}
      </p>

      {err && <p className="text-sm text-red-600">{err}</p>}
      {ok && <p className="text-sm text-emerald-700">{ok}</p>}
    </section>
  );
}
