import { Eye, EyeOff, LockKeyhole, Mail, UserRound } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getApiErrorMessage } from "../services/api";
import { register } from "../services/auth";
import { validateRegistration } from "../utils/validation";

export default function Register() {
  const { user, isLoading } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!isLoading && user) return <Navigate to="/" replace />;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    const validationError = validateRegistration(fullName, email, password, confirmPassword);
    if (validationError) {
      setError(validationError);
      return;
    }

    setSubmitting(true);
    try {
      await register({ full_name: fullName.trim(), email: email.trim(), password });
      setSuccess("Account created. Sign in with your new credentials.");
      window.setTimeout(() => navigate("/login", { replace: true }), 1000);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Registration failed. Check your connection and try again."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#f3f5fa] px-4 py-10">
      <section className="w-full max-w-[460px] rounded-2xl border border-slate-200/80 bg-white p-7 shadow-card sm:p-9">
        <div className="mb-7 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand text-white"><UserRound size={20} /></div>
          <div><p className="text-sm font-semibold text-ink">AIOps Intelligence</p><p className="text-[11px] text-slate-400">Create your workspace account</p></div>
        </div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">Create an account</h1>
        <p className="mt-1.5 mb-7 text-sm text-slate-500">Get started with the AIOps platform foundation</p>
        <form className="space-y-4" onSubmit={handleSubmit}>
          {error && <div role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3.5 py-3 text-sm text-rose-700">{error}</div>}
          {success && <div role="status" className="rounded-lg border border-emerald-200 bg-emerald-50 px-3.5 py-3 text-sm text-emerald-700">{success}</div>}
          <label className="form-label">Full name<span className="input-wrap"><UserRound size={17} /><input autoComplete="name" required minLength={2} maxLength={120} value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Your name" /></span></label>
          <label className="form-label">Email address<span className="input-wrap"><Mail size={17} /><input type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" /></span></label>
          <label className="form-label">Password<span className="input-wrap"><LockKeyhole size={17} /><input type={showPassword ? "text" : "password"} autoComplete="new-password" required minLength={12} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="At least 12 characters" /><button type="button" className="text-slate-400 hover:text-slate-600" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></span></label>
          <label className="form-label">Confirm password<span className="input-wrap"><LockKeyhole size={17} /><input type="password" autoComplete="new-password" required value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} placeholder="Enter your password again" /></span></label>
          <p className="text-[11px] leading-5 text-slate-400">New accounts receive the Viewer role. An administrator can grant elevated access.</p>
          <button type="submit" disabled={submitting} className="primary-button w-full">{submitting ? "Creating account..." : "Create account"}</button>
        </form>
        <div className="mt-6 border-t border-slate-100 pt-5 text-center text-xs text-slate-500">Already registered? <Link to="/login" className="font-semibold text-brand hover:text-blue-700">Sign in</Link></div>
      </section>
    </main>
  );
}
