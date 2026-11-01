import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { HostMetricSample } from "../../types/api";

type MetricChartStatus = "loading" | "error" | "ready";

export function HostMetricChart({
  metric,
  samples,
  status,
  error,
  lastUpdated,
}: {
  metric: "cpu" | "memory";
  samples: HostMetricSample[];
  status: MetricChartStatus;
  error: string | null;
  lastUpdated: string | null;
}) {
  const color = metric === "cpu" ? "#5277e8" : "#10a781";
  const label = metric === "cpu" ? "CPU usage" : "Memory usage";
  const valueKey = metric === "cpu" ? "cpu_percent" : "memory_percent";
  const chartData = samples.map((sample) => ({
    timestamp: sample.timestamp,
    value: sample[valueKey],
  }));

  return (
    <section className="panel p-5">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-ink">Windows host {label.toLowerCase()} trend</h3>
          <p className="mt-1 text-xs text-slate-400">Live Windows Exporter telemetry</p>
        </div>
        <span className="rounded-md border border-blue-200 bg-blue-50 px-2 py-1 text-[10px] font-semibold tracking-wide text-blue-700">
          WINDOWS HOST
        </span>
      </div>
      <div className="h-[210px] w-full">
        {status === "loading" ? (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">
            Loading Windows host metrics...
          </div>
        ) : status === "error" ? (
          <div
            role="alert"
            className="flex h-full items-center justify-center rounded-lg border border-rose-200 bg-rose-50 px-4 text-center text-sm text-rose-700"
          >
            {error}
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">
            No Windows host {label.toLowerCase()} samples are available.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 8, right: 7, left: -20, bottom: 0 }}>
              <CartesianGrid stroke="#edf0f5" strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value: string) =>
                  new Date(value).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                }
                tick={{ fill: "#98a1b2", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                domain={[0, 100]}
                tickFormatter={(value: number) => `${value}%`}
                tick={{ fill: "#98a1b2", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                labelFormatter={(value) => new Date(String(value)).toLocaleString()}
                formatter={(value) => [`${Number(value).toFixed(1)}%`, label]}
              />
              <Line
                type="monotone"
                dataKey="value"
                name={label}
                stroke={color}
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 4, strokeWidth: 0 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
      <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-400">
        <span className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
          {label} (%)
        </span>
        <span>
          Last updated:{" "}
          {lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : "Not yet updated"}
        </span>
      </div>
    </section>
  );
}
