import { Bell, LogOut, Menu, X } from "lucide-react";
import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { useAuth, useSignOutAndNavigate } from "../../context/AuthContext";
import { Sidebar } from "./Sidebar";

const pageTitles: Record<string, string> = {
  "/": "Dashboard",
  "/monitoring": "Infrastructure Monitoring",
  "/logs": "Logs",
  "/anomalies": "Anomaly Detection",
  "/predictions": "Predictive Analytics",
  "/incidents": "Incidents",
  "/ai-insights": "AI Insights",
  "/knowledge": "Knowledge Base",
  "/operations": "Autonomous Operations",
  "/deployments": "Deployments",
  "/audit": "Audit Logs",
  "/settings": "Settings",
};

export function AppLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user } = useAuth();
  const signOutAndNavigate = useSignOutAndNavigate();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-canvas md:flex">
      <div className="hidden md:block">
        <Sidebar />
      </div>
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <Sidebar onNavigate={() => setMobileMenuOpen(false)} />
          <button
            type="button"
            className="flex-1 bg-slate-950/40 p-4 text-white"
            aria-label="Close navigation"
            onClick={() => setMobileMenuOpen(false)}
          >
            <X className="ml-auto" />
          </button>
        </div>
      )}
      <main className="min-w-0 flex-1">
        <header className="sticky top-0 z-20 flex h-[76px] items-center justify-between border-b border-slate-200/80 bg-white/90 px-5 backdrop-blur md:px-8">
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 md:hidden"
              aria-label="Open navigation"
              onClick={() => setMobileMenuOpen(true)}
            >
              <Menu size={19} />
            </button>
            <div>
              <p className="text-[11px] font-medium text-slate-400">AIOps Platform / Workspace</p>
              <h1 className="mt-0.5 text-base font-semibold text-ink">
                {pageTitles[location.pathname] ?? "Workspace"}
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs font-medium text-slate-600 sm:inline-flex">
              Local environment
            </span>
            <span className="hidden text-xs text-slate-400 lg:inline">
              {new Intl.DateTimeFormat(undefined, {
                weekday: "short",
                month: "short",
                day: "numeric",
              }).format(new Date())}
            </span>
            <button
              type="button"
              className="relative rounded-lg p-2 text-slate-500 hover:bg-slate-100"
              aria-label="Notifications (not connected)"
              title="Notifications are not connected in Phase 1"
            >
              <Bell size={18} />
              <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-slate-300" />
            </button>
            <div className="hidden h-8 w-px bg-slate-200 sm:block" />
            <div className="hidden text-right sm:block">
              <p className="max-w-36 truncate text-xs font-semibold text-slate-700">
                {user?.full_name}
              </p>
              <p className="text-[10px] capitalize text-slate-400">
                {user?.role.replaceAll("_", " ")}
              </p>
            </div>
            <button
              type="button"
              onClick={signOutAndNavigate}
              className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50"
              aria-label="Sign out"
              title="Sign out"
            >
              <LogOut size={15} />
              <span className="hidden md:inline">Sign out</span>
            </button>
          </div>
        </header>
        <div className="mx-auto max-w-[1500px] px-5 py-7 md:px-8 md:py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
