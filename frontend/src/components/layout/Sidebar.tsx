import {
  Activity,
  AlertTriangle,
  BarChart3,
  BookOpen,
  Boxes,
  BrainCircuit,
  ChevronLeft,
  CircleGauge,
  ClipboardList,
  Cloud,
  LayoutDashboard,
  ScrollText,
  Settings,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const sections = [
  {
    label: "WORKSPACE",
    items: [
      { label: "Dashboard", to: "/", icon: LayoutDashboard },
      { label: "Infrastructure", to: "/monitoring", icon: Boxes },
      { label: "Logs", to: "/logs", icon: ScrollText },
      { label: "Anomaly Detection", to: "/anomalies", icon: Activity },
      { label: "Predictive Analytics", to: "/predictions", icon: BarChart3 },
      { label: "Incidents", to: "/incidents", icon: AlertTriangle },
    ],
  },
  {
    label: "INTELLIGENCE",
    items: [
      { label: "AI Insights", to: "/ai-insights", icon: BrainCircuit },
      { label: "Knowledge Base", to: "/knowledge", icon: BookOpen },
      { label: "Autonomous Operations", to: "/operations", icon: Workflow },
    ],
  },
  {
    label: "MANAGEMENT",
    items: [
      { label: "Deployments", to: "/deployments", icon: Cloud },
      { label: "Audit Logs", to: "/audit", icon: ShieldCheck },
      { label: "Settings", to: "/settings", icon: Settings },
    ],
  },
];

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <aside className="flex h-screen w-[258px] shrink-0 flex-col bg-sidebar text-slate-300">
      <div className="flex h-[76px] items-center gap-3 border-b border-white/[0.08] px-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand text-white">
          <CircleGauge size={20} />
        </div>
        <div>
          <p className="text-sm font-semibold tracking-wide text-white">AIOps Intelligence</p>
          <p className="mt-0.5 text-[10px] uppercase tracking-[0.16em] text-slate-500">
            Operations platform
          </p>
        </div>
      </div>
      <nav className="custom-scrollbar flex-1 space-y-6 overflow-y-auto px-3 py-6">
        {sections.map((section) => (
          <div key={section.label}>
            <p className="mb-2 px-3 text-[10px] font-semibold tracking-[0.16em] text-slate-500">
              {section.label}
            </p>
            <div className="space-y-1">
              {section.items.map(({ label, to, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === "/"}
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] transition-colors ${
                      isActive
                        ? "bg-brand/15 font-medium text-white"
                        : "text-slate-400 hover:bg-white/[0.05] hover:text-slate-100"
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <Icon size={17} className={isActive ? "text-blue-300" : "text-slate-500"} />
                      <span className="flex-1">{label}</span>
                      {isActive && <ChevronLeft size={14} className="rotate-180 text-blue-300" />}
                    </>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>
      <div className="border-t border-white/[0.08] p-4">
        <div className="rounded-xl border border-white/[0.07] bg-white/[0.035] p-3">
          <div className="flex items-center gap-2 text-xs font-medium text-slate-300">
            <span className="h-2 w-2 rounded-full bg-amber-400" />
            Demo environment
          </div>
          <p className="mt-1.5 pl-4 text-[11px] leading-4 text-slate-500">
            Live telemetry is not connected
          </p>
        </div>
      </div>
    </aside>
  );
}
