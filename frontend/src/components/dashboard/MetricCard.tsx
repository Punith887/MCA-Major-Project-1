import type { LucideIcon } from "lucide-react";

export function MetricCard({
  label,
  value,
  detail,
  icon: Icon,
  accent,
}: {
  label: string;
  value: number | string;
  detail: string;
  icon: LucideIcon;
  accent: "blue" | "green" | "amber" | "red";
}) {
  const colors = {
    blue: "bg-blue-50 text-blue-600",
    green: "bg-emerald-50 text-emerald-600",
    amber: "bg-amber-50 text-amber-600",
    red: "bg-rose-50 text-rose-600",
  }[accent];

  return (
    <article className="panel p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-500">{label}</p>
          <p className="mt-3 text-[27px] font-semibold leading-none tracking-tight text-ink">
            {value}
          </p>
        </div>
        <div className={`rounded-xl p-2.5 ${colors}`}>
          <Icon size={18} />
        </div>
      </div>
      <p className="mt-4 text-[11px] text-slate-400">{detail}</p>
    </article>
  );
}
