import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const demoSeries = [
  { time: "09:00", cpu: 38, memory: 54 },
  { time: "09:10", cpu: 42, memory: 55 },
  { time: "09:20", cpu: 36, memory: 56 },
  { time: "09:30", cpu: 49, memory: 57 },
  { time: "09:40", cpu: 45, memory: 59 },
  { time: "09:50", cpu: 54, memory: 58 },
  { time: "10:00", cpu: 48, memory: 61 },
  { time: "10:10", cpu: 57, memory: 62 },
];

export function DemoMetricChart({
  metric,
}: {
  metric: "cpu" | "memory";
}) {
  const color = metric === "cpu" ? "#5277e8" : "#10a781";
  const label = metric === "cpu" ? "CPU usage" : "Memory usage";
  return (
    <section className="panel p-5">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-ink">{label} trend</h3>
          <p className="mt-1 text-xs text-slate-400">Illustrative values only · not live telemetry</p>
        </div>
        <span className="rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-[10px] font-semibold tracking-wide text-amber-700">
          DEMO DATA
        </span>
      </div>
      <div className="h-[210px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={demoSeries} margin={{ top: 8, right: 7, left: -20, bottom: 0 }}>
            <CartesianGrid stroke="#edf0f5" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="time" tick={{ fill: "#98a1b2", fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis domain={[0, 100]} tick={{ fill: "#98a1b2", fontSize: 10 }} axisLine={false} tickLine={false} />
            <Tooltip formatter={(value) => [`${value}%`, label]} />
            <Line
              type="monotone"
              dataKey={metric}
              stroke={color}
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 0 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 flex items-center gap-2 text-[10px] text-slate-400">
        <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
        {label}
      </div>
    </section>
  );
}
