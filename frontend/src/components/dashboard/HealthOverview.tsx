import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const palette = ["#10a781", "#f3a528", "#e45665", "#cbd5e1"];

export function HealthOverview({
  healthy,
  warning,
  critical,
  unknown,
}: {
  healthy: number;
  warning: number;
  critical: number;
  unknown: number;
}) {
  const items = [
    { name: "Healthy", value: healthy },
    { name: "Warning", value: warning },
    { name: "Critical", value: critical },
    { name: "Unknown", value: unknown },
  ];
  const total = items.reduce((sum, item) => sum + item.value, 0);

  return (
    <section className="panel p-5">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-ink">Infrastructure health</h3>
          <p className="mt-1 text-xs text-slate-400">Database-backed resource status</p>
        </div>
        <span className="rounded-md bg-slate-100 px-2 py-1 text-[10px] font-medium text-slate-500">
          {total} resources
        </span>
      </div>
      {total === 0 ? (
        <div className="flex h-[215px] flex-col items-center justify-center text-center">
          <div className="relative mb-3 flex h-24 w-24 items-center justify-center rounded-full border-[10px] border-slate-100">
            <span className="text-xl font-semibold text-slate-400">0</span>
          </div>
          <p className="text-xs font-medium text-slate-500">No resources registered</p>
          <p className="mt-1 text-[11px] text-slate-400">Monitoring is not connected yet</p>
        </div>
      ) : (
        <div className="flex h-[215px] items-center">
          <div className="h-full w-1/2">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={items} dataKey="value" nameKey="name" innerRadius={55} outerRadius={78} paddingAngle={3}>
                  {items.map((item, index) => (
                    <Cell key={item.name} fill={palette[index]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-3">
            {items.map((item, index) => (
              <div key={item.name} className="flex items-center gap-2 text-xs">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: palette[index] }} />
                <span className="text-slate-500">{item.name}</span>
                <span className="ml-auto pl-2 font-semibold text-slate-700">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
