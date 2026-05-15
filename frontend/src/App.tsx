import { Routes, Route, Link, useLocation } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import CampaignNew from "./pages/CampaignNew";
import CampaignRun from "./pages/CampaignRun";

const NAV = [
  { to: "/", label: "Dashboard" },
  { to: "/campaigns/new", label: "New Campaign" },
  { to: "/leads", label: "Leads" },
];

export default function App() {
  const location = useLocation();
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-sandstone-200 bg-white">
        <div className="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <span className="text-2xl font-serif-display font-bold text-terracotta-600">
              Niaga
            </span>
            <span className="text-xs uppercase tracking-widest text-sandstone-500">
              Autonomous Sales Team
            </span>
          </Link>
          <nav className="flex gap-6 text-sm">
            {NAV.map((n) => (
              <Link
                key={n.to}
                to={n.to}
                className={
                  location.pathname === n.to
                    ? "text-terracotta-600 font-semibold"
                    : "text-sandstone-700 hover:text-terracotta-600"
                }
              >
                {n.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/campaigns/new" element={<CampaignNew />} />
          <Route path="/campaigns/:id/run" element={<CampaignRun />} />
          <Route
            path="/leads"
            element={<Placeholder title="Lead Kanban" note="See Campaign Run page for the live demo view." />}
          />
        </Routes>
      </main>
      <footer className="border-t border-sandstone-200 bg-white">
        <div className="mx-auto max-w-7xl px-6 py-3 text-xs text-sandstone-500">
          Team Juwara · OpenClaw Agenthon 2026
        </div>
      </footer>
    </div>
  );
}

function Placeholder({ title, note }: { title: string; note: string }) {
  return (
    <div className="mx-auto max-w-3xl px-6 py-16 text-center">
      <h1 className="text-3xl font-serif-display font-bold text-sandstone-900">
        {title}
      </h1>
      <p className="mt-3 text-sandstone-600">{note}</p>
    </div>
  );
}
