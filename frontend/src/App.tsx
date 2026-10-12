import { useState, type FormEvent } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

// -------------------- TYPES --------------------

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
  application_date: string | null;
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

type Benefit = {
  scheme_id: number;
  scheme_name: string;
  description: string;
  category: string;
  source_url: string;
  status: string;
  missing_fields: string[];
  reasons: string[];
};

// -------------------- APP --------------------

function App() {
  const [mobile, setMobile] = useState("");
  const [password, setPassword] = useState("");

  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [benefits, setBenefits] = useState<Benefit[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [benefitsError, setBenefitsError] = useState("");

  // -------------------- LOGIN --------------------

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setBenefitsError("");

    try {
      const loginResponse = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ mobile, password }),
      });

      if (!loginResponse.ok) {
        throw new Error(
          loginResponse.status === 401
            ? "Mobile number ya password galat hai."
            : "Login nahi ho paya. Backend check karo.",
        );
      }

      const loginData: {
        access_token: string;
        token_type: string;
      } = await loginResponse.json();

      const headers = {
        Authorization: `Bearer ${loginData.access_token}`,
      };

      // User aur dashboard data parallel mein load hoga.
      const [userResponse, dashboardResponse] = await Promise.all([
        fetch(`${API_URL}/auth/me`, { headers }),
        fetch(`${API_URL}/dashboard/me`, { headers }),
      ]);

      if (
        userResponse.status === 401 ||
        dashboardResponse.status === 401
      ) {
        throw new Error("Session validate nahi hua. Dobara login karo.");
      }

      if (!userResponse.ok || !dashboardResponse.ok) {
        throw new Error("Dashboard load nahi hua. Dobara try karo.");
      }

      const userData: User = await userResponse.json();
      const dashboardData: DashboardData =
        await dashboardResponse.json();

      setToken(loginData.access_token);
      setUser(userData);
      setDashboard(dashboardData);

      // Benefits request separate hai.
      // Benefits fail hone par dashboard accessible rahega.
      try {
        const benefitsResponse = await fetch(
          `${API_URL}/benefits/me`,
          { headers },
        );

        if (!benefitsResponse.ok) {
          throw new Error("Benefits API ne error return kiya.");
        }

        const benefitsData: Benefit[] =
          await benefitsResponse.json();

        setBenefits(benefitsData);
      } catch {
        setBenefits([]);
        setBenefitsError(
          "Benefits load nahi ho paaye. Thodi der baad retry karo.",
        );
      }
    } catch (err) {
      setError(
        err instanceof TypeError
          ? "Backend se connection nahi ho raha. FastAPI check karo."
          : err instanceof Error
            ? err.message
            : "Kuch unexpected problem hui.",
      );
    } finally {
      setLoading(false);
    }
  }

  // -------------------- LOGOUT --------------------

  function handleLogout() {
    setToken(null);
    setUser(null);
    setDashboard(null);
    setBenefits([]);

    setPassword("");
    setError("");
    setBenefitsError("");
  }

  // -------------------- LOGIN PAGE --------------------

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

            {error && (
              <p className="error-message" role="alert">
                {error}
              </p>
            )}

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

  // -------------------- DASHBOARD --------------------

  return (
    <main className="dashboard-page">
      {/* HEADER */}

      <header className="dashboard-header">
        <div>
          <p className="eyebrow">SHRAMMITRA WORKER PORTAL</p>

          <h1>Namaste, {user.full_name}</h1>

          <p className="muted">
            Apni applications, benefits aur support track karo.
          </p>
        </div>

        <button
          className="secondary-button"
          onClick={handleLogout}
        >
          Logout
        </button>
      </header>

      {/* DASHBOARD STATISTICS */}

      <section
        className="stats-grid"
        aria-label="Dashboard summary"
      >
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

      {/* BENEFITS */}

      <section className="content-section">
        <h2>Benefits for you</h2>

        <p className="muted">
          Ye results tumhare available worker profile aur configured
          rules par based hain. Final eligibility concerned
          government department decide karega.
        </p>

        {benefitsError ? (
          <p className="error-message" role="alert">
            {benefitsError}
          </p>
        ) : benefits.length === 0 ? (
          <p className="empty-state">
            Abhi koi benefit result nahi mila. Worker profile
            complete karo aur check karo ki active schemes ke
            eligibility rules configured hain.
          </p>
        ) : (
          <div className="item-list">
            {benefits.map((benefit) => (
              <article
                className="item-card"
                key={benefit.scheme_id}
              >
                <p className="eyebrow">{benefit.category}</p>

                <div className="item-heading">
                  <h3>{benefit.scheme_name}</h3>

                  <span className="status-pill">
                    {benefit.status}
                  </span>
                </div>

                <p>{benefit.description}</p>

                {/* MISSING INFORMATION */}

                {benefit.status === "Missing Information" &&
                  benefit.missing_fields.length > 0 && (
                    <div className="next-action">
                      <strong>Information needed</strong>

                      <ul>
                        {benefit.missing_fields.map((field) => (
                          <li key={field}>
                            {field.replaceAll("_", " ")}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                {/* POTENTIAL ELIGIBILITY NOTICE */}

                {benefit.status === "Potentially Eligible" && (
                  <p className="muted">
                    Initial rule check match hua hai. Official
                    verification abhi bhi required ho sakti hai.
                  </p>
                )}

                {/* ELIGIBILITY EXPLANATION */}

                <div className="benefit-reasons">
                  <h4>Why this result?</h4>

                  {benefit.reasons.length > 0 ? (
                    <ul>
                      {benefit.reasons.map((reason, index) => (
                        <li key={`${benefit.scheme_id}-${index}`}>
                          {reason}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="muted">
                      Is result ki detailed explanation available
                      nahi hai.
                    </p>
                  )}
                </div>

                {/* OFFICIAL SOURCE */}

                {benefit.source_url && (
                  <p>
                    <a
                      href={benefit.source_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Official scheme source ↗
                    </a>
                  </p>
                )}
              </article>
            ))}
          </div>
        )}
      </section>

      {/* APPLICATIONS */}

      <section className="content-section">
        <h2>Your applications</h2>

        {dashboard.applications.length === 0 ? (
          <p className="empty-state">
            Abhi koi application track nahi ho rahi.
          </p>
        ) : (
          <div className="item-list">
            {dashboard.applications.map((application) => (
              <article
                className="item-card"
                key={application.id}
              >
                <div className="item-heading">
                  <h3>{application.scheme_name}</h3>

                  <span className="status-pill">
                    {application.status.replaceAll("_", " ")}
                  </span>
                </div>

                <p className="muted">
                  {application.scheme_category}
                </p>

                <p className="muted">
                  Reference:{" "}
                  {application.reference_number || "Not available"}
                </p>

                <p>
                  {application.days_in_current_status === null
                    ? "Application status is final."
                    : `${application.days_in_current_status} day(s) in current status`}
                </p>

                <div className="next-action">
                  <strong>Next action</strong>

                  <p>
                    {application.next_action ||
                      "Check official application updates."}
                  </p>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      {/* GRIEVANCES */}

      <section className="content-section">
        <h2>Your grievances</h2>

        {dashboard.grievances.length === 0 ? (
          <p className="empty-state">
            Abhi koi grievance listed nahi hai.
          </p>
        ) : (
          <div className="item-list">
            {dashboard.grievances.map((grievance) => (
              <article
                className="item-card"
                key={grievance.id}
              >
                <div className="item-heading">
                  <h3>{grievance.subject}</h3>

                  <span className="status-pill">
                    {grievance.status.replaceAll("_", " ")}
                  </span>
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