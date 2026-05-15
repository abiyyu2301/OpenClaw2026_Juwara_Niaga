import { Routes, Route } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import Dashboard from "./pages/Dashboard";
import CampaignNew from "./pages/CampaignNew";
import CampaignEdit from "./pages/CampaignEdit";
import CampaignOverview from "./pages/CampaignOverview";
import CampaignRun from "./pages/CampaignRun";

export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/campaigns/new" element={<CampaignNew />} />
        <Route path="/campaigns/:id/edit" element={<CampaignEdit />} />
        <Route path="/campaigns/:id/run" element={<CampaignRun />} />
        <Route path="/campaigns/:id" element={<CampaignOverview />} />
      </Routes>
    </AppLayout>
  );
}
