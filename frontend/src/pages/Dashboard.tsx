import { useEffect, useState } from "react";

interface Health {
  status: string;
  service: string;
}

export default function Dashboard() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then(setHealth)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div className="mx-auto max-w-7xl px-6 py-12">
      <div className="mb-12">
        <h1 className="text-4xl font-serif-display font-bold text-sandstone-900">
          Hello, Tim Juwara.
        </h1>
        <p className="mt-2 text-sandstone-600">
          Your autonomous AI sales team is ready to start prospecting.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard label="Leads processed" value="0" />
        <StatCard label="Qualified" value="0" />
        <StatCard label="Emails sent" value="0" />
        <StatCard label="Revenue collected" value="Rp 0" />
      </div>

      <div className="mt-12 rounded-lg border border-sandstone-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-sandstone-900">
          Backend connection
        </h2>
        {error && (
          <p className="mt-2 text-sm text-red-600 font-mono-feed">
            ✗ {error}
          </p>
        )}
        {!error && !health && (
          <p className="mt-2 text-sm text-sandstone-500">Checking…</p>
        )}
        {health && (
          <p className="mt-2 text-sm text-green-700 font-mono-feed">
            ✓ {health.service} — {health.status}
          </p>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-sandstone-200 bg-white p-5">
      <p className="text-xs uppercase tracking-wider text-sandstone-500">
        {label}
      </p>
      <p className="mt-1 text-3xl font-serif-display font-bold text-terracotta-600">
        {value}
      </p>
    </div>
  );
}
