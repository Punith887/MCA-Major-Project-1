import { Eye, EyeOff, LockKeyhole, Mail, ShieldCheck } from "lucide-react";
import { useState, type FormEvent } from "react";
import type { ReactNode } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getApiErrorMessage } from "../services/api";

export default function Login() {
  const { user, signIn, isLoading } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!isLoading && user) return <Navigate to="/" replace />;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await signIn(email.trim(), password);
      navigate("/", { replace: true });
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Sign in failed. Check your connection and try again."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to your AIOps workspace"
      footer={<>New to the platform? <Link to="/register" className="font-semibold text-brand hover:text-blue-700">Create an account</Link></>}
    >
      <form className="space-y-5" onSubmit={handleSubmit}>
        {error && <div role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3.5 py-3 text-sm text-rose-700">{error}</div>}
        <label className="form-label">
          Email address
          <span className="input-wrap"><Mail size={17} /><input type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" /></span>
        </label>
        <label className="form-label">
          Password
          <span className="input-wrap">
            <LockKeyhole size={17} />
            <input type={showPassword ? "text" : "password"} autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Enter your password" />
            <button type="button" className="text-slate-400 hover:text-slate-600" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button>
          </span>
        </label>
        <button type="submit" disabled={submitting} className="primary-button w-full">
          {submitting ? "Signing in..." : "Sign in"}
        </button>
        <p className="flex items-center justify-center gap-1.5 text-[11px] text-slate-400"><ShieldCheck size={14} /> Your account is protected with secure authentication</p>
      </form>
    </AuthShell>
  );
}

function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#f3f5fa] px-4 py-10">
      <section className="w-full max-w-[440px] rounded-2xl border border-slate-200/80 bg-white p-7 shadow-card sm:p-9">
        <div className="mb-7 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand text-white"><ShieldCheck size={21} /></div>
          <div><p className="text-sm font-semibold text-ink">AIOps Intelligence</p><p className="text-[11px] text-slate-400">Operations platform</p></div>
        </div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">{title}</h1>
        <p className="mt-1.5 mb-7 text-sm text-slate-500">{subtitle}</p>
        {children}
        <div className="mt-7 border-t border-slate-100 pt-5 text-center text-xs text-slate-500">{footer}</div>
        <p className="mt-5 text-center text-[10px] text-slate-400">Phase 1 foundation · Monitoring integrations are not connected</p>
      </section>
    </main>
  );
}
