import { useState } from "react";
import { Activity, BrainCircuit, LockKeyhole, Mail } from "lucide-react";
import { loginUser } from "./services/auth";
import "./Login.css";

function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const user = await loginUser(username.trim(), password);

      if (!user.is_active) {
        sessionStorage.removeItem("access_token");
        throw new Error("This account is inactive. Contact your administrator.");
      }

      onLogin(user);
    } catch (err) {
      setError(err.message || "Unable to sign in. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-screen">
      <div className="login-glow login-glow-one" />
      <div className="login-glow login-glow-two" />

      <section className="login-card">
        <div className="login-brand-icon">
          <Activity size={27} />
        </div>

        <div className="login-brand">
          WorkForce<span>AI</span>
        </div>
        <p className="login-subtitle">WORKFORCE INTELLIGENCE PLATFORM</p>

        <div className="login-divider" />

        <div className="login-heading">
          <span className="login-heading-icon">
            <BrainCircuit size={20} />
          </span>
          <div>
            <h1>Welcome back</h1>
            <p>Sign in to access your workspace.</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <label htmlFor="login-username">Email address</label>
          <div className="login-input-wrap">
            <Mail size={18} />
            <input
              id="login-username"
              type="email"
              autoComplete="username"
              placeholder="you@company.com"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
          </div>

          <label htmlFor="login-password">Password</label>
          <div className="login-input-wrap">
            <LockKeyhole size={18} />
            <input
              id="login-password"
              type="password"
              autoComplete="current-password"
              placeholder="Enter your password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>

          {error && (
            <div className="login-error" role="alert">
              {error}
            </div>
          )}

          <button className="login-submit" type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Sign in to workspace"}
            {!loading && <span>→</span>}
          </button>
        </form>

        <div className="login-security">
          <LockKeyhole size={16} />
          <span>Secure sign-in · Role-based access</span>
        </div>
      </section>

      <p className="login-footer">
        © 2026 WorkForce AI Pro · Responsible workforce intelligence
      </p>
    </main>
  );
}

export default Login;
