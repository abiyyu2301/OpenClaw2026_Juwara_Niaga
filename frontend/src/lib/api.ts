/** Lightweight typed API client. Talks to /api which Vite proxies to :8000. */

const BASE = "/api";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { ...(init?.headers as Record<string, string>) };
  const isForm = init?.body instanceof FormData;
  if (!isForm) headers["Content-Type"] = "application/json";

  const r = await fetch(BASE + path, { ...init, headers });
  if (!r.ok) {
    const text = await r.text().catch(() => "");
    throw new Error(`${r.status} ${r.statusText}: ${text || path}`);
  }
  return r.status === 204 ? (undefined as T) : ((await r.json()) as T);
}

export interface Campaign {
  id: number;
  name: string;
  target_industry?: string;
  company_size?: string;
  geography?: string;
  buyer_role?: string;
  pain_points?: string;
  offer?: string;
  pricing_range_min?: number;
  pricing_range_max?: number;
  currency: string;
  disqualifiers?: string;
  autonomous_mode: boolean;
  max_leads_per_run: number;
  created_at: string;
  sales_target_revenue?: number;
  geo_place_name?: string;
  geo_lat?: number;
  geo_lng?: number;
  geo_radius_km?: number;
  rep_name?: string;
  rep_email?: string;
  rep_phone?: string;
  rep_title?: string;
  sales_voice?: string;
  sales_voice_samples?: string;
  promo_asset_url?: string;
  promo_asset_type?: string;
  suggested_max_leads?: number;
}

export interface CampaignSummary {
  id: number;
  name: string;
  target_industry?: string;
  geography?: string;
  geo_place_name?: string;
  offer?: string;
  currency: string;
  max_leads_per_run: number;
  sales_target_revenue?: number;
  created_at: string;
  leads_total: number;
  leads_processed: number;
  leads_qualified: number;
  emails_sent: number;
  deals_closed: number;
  total_revenue: number;
  last_run_status?: string;
  last_run_at?: string;
  active_run_id?: number;
  qualify_rate: number;
  close_rate: number;
}

export interface DashboardStats {
  leads_processed: number;
  leads_qualified: number;
  emails_sent: number;
  deals_closed: number;
  total_revenue: number;
  qualify_rate: number;
  outreach_rate: number;
  close_rate: number;
  revenue_per_deal: number;
  campaigns: CampaignSummary[];
  maps_api_configured: boolean;
}

export interface CampaignAsset {
  id: number;
  campaign_id: number;
  file_name?: string;
  mime_type?: string;
  asset_type?: string;
  storage_url: string;
  created_at: string;
}

export interface Lead {
  id: number;
  campaign_id: number;
  company_name: string;
  industry?: string;
  website?: string;
  buyer_name?: string;
  buyer_role?: string;
  email?: string;
  raw_notes?: string;
  status: string;
  created_at: string;
}

export interface Run {
  id: number;
  campaign_id: number;
  started_at?: string;
  ended_at?: string;
  leads_processed: number;
  leads_qualified: number;
  emails_sent: number;
  deals_closed: number;
  total_revenue: number;
  total_tokens: number;
  status: string;
  error_message?: string;
}

export interface AgentMessage {
  id: number;
  run_id: number;
  lead_id?: number;
  agent_name: string;
  role: string;
  content?: string;
  model?: string;
  prompt_tokens: number;
  completion_tokens: number;
  latency_ms?: number;
  created_at: string;
}

export const api = {
  getPublicConfig: () =>
    req<{ maps_api_key: string | null; currencies: string[] }>("/campaigns/config/public"),

  getDashboard: () => req<DashboardStats>("/campaigns/dashboard"),

  listCampaigns: () => req<Campaign[]>("/campaigns"),
  getCampaign: (id: number) => req<Campaign>(`/campaigns/${id}`),
  createCampaign: (payload: Partial<Campaign>) =>
    req<Campaign>("/campaigns", { method: "POST", body: JSON.stringify(payload) }),
  updateCampaign: (id: number, payload: Partial<Campaign>) =>
    req<Campaign>(`/campaigns/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),

  uploadAsset: async (campaignId: number, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return req<CampaignAsset>(`/campaigns/${campaignId}/assets`, { method: "POST", body: fd });
  },

  listLeads: (campaignId?: number, status?: string) => {
    const q = new URLSearchParams();
    if (campaignId !== undefined) q.set("campaign_id", String(campaignId));
    if (status) q.set("status", status);
    const qs = q.toString();
    return req<Lead[]>(`/leads${qs ? `?${qs}` : ""}`);
  },
  createLead: (payload: Partial<Lead> & { campaign_id: number; company_name: string }) =>
    req<Lead>("/leads", { method: "POST", body: JSON.stringify(payload) }),
  updateLead: (id: number, payload: Partial<Lead>) =>
    req<Lead>(`/leads/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  createLeadsBulk: (payload: {
    campaign_id: number;
    leads: Array<{ company_name: string; email?: string; buyer_name?: string; industry?: string }>;
  }) => req<Lead[]>("/leads/bulk", { method: "POST", body: JSON.stringify(payload) }),
  importLeadsCsv: async (campaignId: number, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return req<Lead[]>(`/leads/import-csv?campaign_id=${campaignId}`, { method: "POST", body: fd });
  },
  getEmailStatus: () =>
    req<{ configured: boolean; dry_run: boolean; from_address?: string; message: string }>(
      "/leads/email-status",
    ),
  sendTestEmail: (to_address: string) =>
    req<{ ok: boolean; message_id: string; dry_run: boolean }>("/leads/test-send", {
      method: "POST",
      body: JSON.stringify({ to_address }),
    }),
  getLead: (id: number) =>
    req<{ lead: Lead; profile: any; debate: any }>(`/leads/${id}`),

  startRun: (campaign_id: number) =>
    req<Run>(`/runs/start?campaign_id=${campaign_id}`, { method: "POST" }),
  pauseRun: (id: number) => req<Run>(`/runs/${id}/pause`, { method: "POST" }),
  resumeRun: (id: number) => req<Run>(`/runs/${id}/resume`, { method: "POST" }),
  stopRun: (id: number) => req<Run>(`/runs/${id}/stop`, { method: "POST" }),
  listRuns: () => req<Run[]>("/runs"),
  getRun: (id: number) => req<Run>(`/runs/${id}`),
  getRunMessages: (id: number, limit = 500) =>
    req<AgentMessage[]>(`/runs/${id}/messages?limit=${limit}`),

  simulatePay: (referenceId: string, status: "paid" | "failed" | "expired") =>
    req<{ ok: boolean }>(`/webhooks/mock-pay/${referenceId}?status=${status}`, { method: "POST" }),

  findLeads: (campaignId: number, n = 3) =>
    req<Lead[]>(`/campaigns/${campaignId}/find-leads?n=${n}`, { method: "POST" }),
};
