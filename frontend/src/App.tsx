
import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

type User = {
  id: number;
  full_name: string;
  mobile: string;
};

type Application = {
  id: number;
  scheme_id: number;
  scheme_name: string;
  scheme_category: string;
  reference_number: string | null;
  status: string;
  application_date: string;
  next_action: string | null;
  days_in_current_status: number | null;
};

type Grievance = {
  id: number;
  subject: string;
  status: string;
  created_at: string;
  days_pending: number | null;
};

type DashboardData = {
  applications_count: number;
  active_applications_count: number;
  open_grievances_count: number;
  applications: Application[];
  grievances: Grievance[];
};

function App() {
  const [mobile, setMobile] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const loginResponse = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mobile, password }),
      });

      if (!loginResponse.ok) {
        throw new Error(
          loginResponse.status === 401
            ? "Mobile number ya password galat hai."
            : "Login nahi ho paya. Backend check karo.",
        );
      }

      const loginData: { access_token: string; token_type: string } =
        await loginResponse.json();

      const headers = {
        Authorization: `Bearer ${loginData.access_token}`,
      };

      const [userResponse, dashboardResponse] = await Promise.all([
        fetch(`${API_URL}/auth/me`, { headers }),
        fetch(`${API_URL}/dashboard/me`, { headers }),
      ]);

      if (userResponse.status === 401 || dashboardResponse.status === 401) {
        throw new Error("Session validate nahi hua. Dobara login karo.");
      }

      if (!userResponse.ok || !dashboardResponse.ok) {
        throw new Error("Dashboard load nahi hua. Dobara try karo.");
      }

      const userData: User = await userResponse.json();
      const dashboardData: DashboardData = await dashboardResponse.json();

      setToken(loginData.access_token);
      setUser(userData);
      setDashboard(dashboardData);
    } catch (err) {
      setError(
        err instanceof TypeError
          ? "Backend se connection nahi ho raha. Check karo ki FastAPI running hai."
          : err instanceof Error
            ? err.message
            : "Kuch unexpected problem hui.",
      );
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    setToken(null);
    setUser(null);
    setDashboard(null);
    setPassword("");
    setError("");
  }

  if (!token || !user || !dashboard) {
    return (
      <main className="login-page">
        <section className="login-card">
          <p className="eyebrow">YOUR BENEFITS. YOUR RIGHTS.</p>
          <h1>ShramMitra</h1>
          <p className="muted">
            Government benefits aur applications, ek hi jagah.
          </p>

          <form onSubmit={handleLogin} className="login-form">
            <label htmlFor="mobile">Mobile number</label>
            <input
              id="mobile"
              type="tel"
              value={mobile}
              onChange={(event) => setMobile(event.target.value)}
              placeholder="Registered mobile number"
              minLength={10}
              maxLength={15}
              autoComplete="username"
              required
            />

            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Your password"
              autoComplete="current-password"
              required
            />

            {error && <p className="error-message" role="alert">{error}</p>}

            <button type="submit" disabled={loading}>
              {loading ? "Signing in..." : "Login to ShramMitra"}
            </button>
          </form>

          <p className="login-note">
            Apne registered account se login karo.
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="dashboard-page">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">SHRAMMITRA WORKER PORTAL</p>
          <h1>Namaste, {user.full_name}</h1>
          <p className="muted">Yahan se apni applications aur support track karo.</p>
        </div>
        <button className="secondary-button" onClick={handleLogout}>
          Logout
        </button>
      </header>

      <section className="stats-grid" aria-label="Dashboard summary">
        <article className="stat-card">
          <p>Total applications</p>
          <strong>{dashboard.applications_count}</strong>
        </article>
        <article className="stat-card">
          <p>Active applications</p>
          <strong>{dashboard.active_applications_count}</strong>
        </article>
        <article className="stat-card">
          <p>Open grievances</p>
          <strong>{dashboard.open_grievances_count}</strong>
        </article>
      </section>

      <section className="content-section">
        <h2>Your applications</h2>
        {dashboard.applications.length === 0 ? (
          <p className="empty-state">Abhi koi application track nahi ho rahi.</p>
        ) : (
          <div className="item-list">
            {dashboard.applications.map((application) => (
              <article className="item-card" key={application.id}>
                <div className="item-heading">
                  <h3>{application.scheme_name}</h3>
                  <p className="muted">{application.scheme_category}</p>
                  <span className="status-pill">{application.status.replaceAll("_", " ")}</span>
                </div>
                <p className="muted">
                  Reference: {application.reference_number || "Not available"}
                </p>
                <p>
                  {application.days_in_current_status === null
                    ? "Application status is final."
                    : `${application.days_in_current_status} day(s) in current status`}
                </p>
                <div className="next-action">
                  <strong>Next action</strong>
                  <p>{application.next_action || "Check official application updates."}</p>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="content-section">
        <h2>Your grievances</h2>
        {dashboard.grievances.length === 0 ? (
          <p className="empty-state">Abhi koi grievance listed nahi hai.</p>
        ) : (
          <div className="item-list">
            {dashboard.grievances.map((grievance) => (
              <article className="item-card" key={grievance.id}>
                <div className="item-heading">
                  <h3>{grievance.subject}</h3>
                  <span className="status-pill">{grievance.status.replaceAll("_", " ")}</span>
                </div>
                <p className="muted">
                  {grievance.days_pending === null
                    ? "Grievance closed."
                    : `Pending for ${grievance.days_pending} day(s)`}
                </p>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

export default App;
