import { useNavigate } from "react-router-dom";
import { CampaignForm } from "../components/CampaignForm";

export default function CampaignNew() {
  const navigate = useNavigate();
  return (
    <CampaignForm
      mode="create"
      onCancel={() => navigate("/")}
      onDone={(c) => navigate(`/campaigns/${c.id}`)}
    />
  );
}
