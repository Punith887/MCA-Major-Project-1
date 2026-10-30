import { ArrowUpRight, Construction } from "lucide-react";

export function PagePlaceholder({
  title,
  description,
  status = "Coming in Phase 2",
}: {
  title: string;
  description: string;
  status?: string;
}) {
  return (
    <section className="panel flex min-h-[360px] flex-col items-center justify-center px-6 py-12 text-center">
      <div className="mb-5 rounded-2xl bg-indigo-50 p-4 text-brand">
        <Construction size={25} />
      </div>
      <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
        {status}
      </span>
      <h2 className="mt-4 text-xl font-semibold text-ink">{title}</h2>
      <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">{description}</p>
      <div className="mt-5 inline-flex items-center gap-1 text-xs text-slate-400">
        This feature is not connected in Phase 1 <ArrowUpRight size={13} />
      </div>
    </section>
  );
}
