import { Link, useLocation } from "react-router-dom";
import { useI18n, type Locale } from "../lib/i18n";

export function AppLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const path = location.pathname;
  const { locale, setLocale, t } = useI18n();

  const NAV = [
    { to: "/", label: t("nav_dashboard"), icon: "▦" },
    { to: "/campaigns/new", label: t("nav_new_campaign"), icon: "+" },
  ];

  function navClass(to: string) {
    const active =
      to === "/" ? path === "/" : path === to || path.startsWith(to + "/");
    return active
      ? "flex items-center gap-3 px-3 py-2.5 rounded-lg bg-stone-800 text-white text-sm font-medium"
      : "flex items-center gap-3 px-3 py-2.5 rounded-lg text-stone-400 hover:text-white hover:bg-stone-800/50 text-sm";
  }

  return (
    <div className="min-h-screen flex bg-stone-100">
      <aside className="w-56 shrink-0 bg-stone-900 text-stone-300 flex flex-col border-r border-stone-800">
        <div className="p-4 border-b border-stone-800">
          <Link to="/" className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-orange-500 text-white text-lg">
              ⚡
            </span>
            <div>
              <div className="font-bold text-white leading-tight">Niaga</div>
              <div className="text-[10px] uppercase tracking-widest text-stone-500">
                AI Sales
              </div>
            </div>
          </Link>
          <p className="mt-3 text-xs flex items-center gap-1.5 text-stone-500">
            <span className="h-1.5 w-1.5 rounded-full bg-orange-500 animate-pulse" />
            {t("agents_ready")}
          </p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {NAV.map((n) => (
            <Link key={n.to} to={n.to} className={navClass(n.to)}>
              <span className="w-5 text-center opacity-80">{n.icon}</span>
              {n.label}
            </Link>
          ))}
        </nav>
        <div className="p-4 border-t border-stone-800 space-y-3">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-stone-500 mb-1.5">
              {t("lang")}
            </p>
            <div className="flex rounded-lg overflow-hidden border border-stone-700 text-xs">
              {(["id", "en"] as Locale[]).map((l) => (
                <button
                  key={l}
                  type="button"
                  onClick={() => setLocale(l)}
                  className={`flex-1 py-1.5 uppercase ${
                    locale === l ? "bg-stone-700 text-white" : "text-stone-500 hover:text-stone-300"
                  }`}
                >
                  {l}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-8 w-8 rounded-full bg-orange-500 text-white text-xs font-bold flex items-center justify-center">
              TJ
            </span>
            <div className="text-xs">
              <p className="text-white font-medium">Tim Juwara</p>
              <p className="text-stone-500">OpenClaw 2026</p>
            </div>
          </div>
        </div>
      </aside>
      <div className="flex-1 flex flex-col min-w-0">{children}</div>
    </div>
  );
}
