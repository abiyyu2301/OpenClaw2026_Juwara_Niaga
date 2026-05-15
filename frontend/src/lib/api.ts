/** Lightweight typed API client. Talks to /api which Vite proxies to :8000. */

const BASE = "/api";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(BASE + path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
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
  // Campaigns
  listCampaigns: () => req<Campaign[]>("/campaigns"),
  getCampaign: (id: number) => req<Campaign>(`/campaigns/${id}`),
  createCampaign: (payload: Partial<Campaign>) =>
    req<Campaign>("/campaigns", { method: "POST", body: JSON.stringify(payload) }),

  // Leads
  listLeads: (campaignId?: number, status?: string) => {
    const q = new URLSearchParams();
    if (campaignId !== undefined) q.set("campaign_id", String(campaignId));
    if (status) q.set("status", status);
    const qs = q.toString();
    return req<Lead[]>(`/leads${qs ? `?${qs}` : ""}`);
  },
  createLead: (payload: Partial<Lead> & { campaign_id: number; company_name: string }) =>
    req<Lead>("/leads", { method: "POST", body: JSON.stringify(payload) }),
  getLead: (id: number) =>
    req<{ lead: Lead; profile: any; debate: any }>(`/leads/${id}`),

  // Runs
  startRun: (campaign_id: number) =>
    req<Run>(`/runs/start?campaign_id=${campaign_id}`, { method: "POST" }),
  pauseRun: (id: number) => req<Run>(`/runs/${id}/pause`, { method: "POST" }),
  resumeRun: (id: number) => req<Run>(`/runs/${id}/resume`, { method: "POST" }),
  stopRun: (id: number) => req<Run>(`/runs/${id}/stop`, { method: "POST" }),
  listRuns: () => req<Run[]>("/runs"),
  getRun: (id: number) => req<Run>(`/runs/${id}`),
  getRunMessages: (id: number, limit = 500) =>
    req<AgentMessage[]>(`/runs/${id}/messages?limit=${limit}`),

  // Mock pay simulation
  simulatePay: (referenceId: string, status: "paid" | "failed" | "expired") =>
    req<{ ok: boolean }>(`/webhooks/mock-pay/${referenceId}?status=${status}`, { method: "POST" }),

  // LeadFinder — discover new leads via grounded Gemini
  findLeads: (campaignId: number, n = 3) =>
    req<Lead[]>(`/campaigns/${campaignId}/find-leads?n=${n}`, { method: "POST" }),
};
