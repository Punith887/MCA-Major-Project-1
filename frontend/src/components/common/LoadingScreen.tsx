export function LoadingScreen({ label = "Loading your workspace..." }: { label?: string }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas">
      <div className="flex items-center gap-3 text-sm font-medium text-slate-600">
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-brand border-t-transparent" />
        {label}
      </div>
    </div>
  );
}
