import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { CampaignForm } from "../components/CampaignForm";
import { api, type Campaign } from "../lib/api";

export default function CampaignEdit() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const campaignId = Number(id);
  const [campaign, setCampaign] = useState<Campaign | null>(null);

  useEffect(() => {
    if (!campaignId) return;
    api.getCampaign(campaignId).then(setCampaign).catch(() => navigate("/"));
  }, [campaignId, navigate]);

  if (!campaign) {
    return <p className="p-10 text-center text-sandstone-600">Memuat…</p>;
  }

  return (
    <CampaignForm
      mode="edit"
      campaignId={campaignId}
      initial={campaign}
      onCancel={() => navigate(`/campaigns/${campaignId}`)}
      onDone={() => navigate(`/campaigns/${campaignId}`)}
    />
  );
}
