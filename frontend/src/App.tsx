
import { useState, type FormEvent } from "react";
import "./App.css";
import AdminDashboard from "./AdminDashboard";

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

// -------------------- WORKER APP --------------------

function WorkerApp() {
  const [mobile, setMobile] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

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

      // Benefits fail hone par bhi dashboard accessible rahega.
      try {
        const benefitsResponse = await fetch(`${API_URL}/benefits/me`, {
          headers,
        });

        if (!benefitsResponse.ok) {
          throw new Error("Benefits API ne error return kiya.");
        }

        const benefitsData: Benefit[] = await benefitsResponse.json();

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
    setShowPassword(false);
    setError("");
    setBenefitsError("");
  }

  // -------------------- LOGIN PAGE --------------------

  if (!token || !user || !dashboard) {
    return (
      <main className="login-page">
        <section className="login-shell">
          {/* LEFT: BRAND EXPERIENCE */}

          <aside className="login-hero">
            <a
              className="brand-mark"
              href="#"
              aria-label="ShramMitra home"
            >
              <span className="brand-symbol" aria-hidden="true">
                <svg viewBox="0 0 40 40" fill="none">
                  <path
                    d="M20 4 34 12v16L20 36 6 28V12L20 4Z"
                    stroke="currentColor"
                    strokeWidth="2"
                  />

                  <path
                    d="M13 21l5 5 10-12"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </span>

              <span>ShramMitra</span>
            </a>

            <div className="hero-copy">
              <p className="hero-kicker">
                <span className="hero-kicker-dot" />

                SUPPORTING THE PEOPLE WHO KEEP US MOVING
              </p>

              <h1>
                Your work
                <br />
                matters.
                <br />

                <span>Your benefits</span>

                <br />
                should too.
              </h1>

              <p className="hero-description">
                Discover government schemes, understand your benefits
                and keep track of your applications — all in one place.
              </p>
            </div>

            {/* Minimal CSS worker illustration */}

            <div className="hero-art" aria-hidden="true">
              <div className="art-orbit art-orbit-one" />
              <div className="art-orbit art-orbit-two" />
              <div className="art-sun" />

              <div className="art-leaf art-leaf-one" />
              <div className="art-leaf art-leaf-two" />

              <div className="worker-illustration">
                <div className="worker-head">
                  <div className="worker-hair" />
                  <div className="worker-helmet" />
                </div>

                <div className="worker-neck" />

                <div className="worker-body">
                  <div className="worker-shirt-line" />
                </div>

                <div className="worker-arm worker-arm-left" />
                <div className="worker-arm worker-arm-right" />

                <div className="worker-bag">
                  <span />
                </div>
              </div>

              <div className="art-ground" />

              <div className="art-building art-building-one" />
              <div className="art-building art-building-two" />
              <div className="art-building art-building-three" />

              <div className="art-note">
                <span className="art-note-icon">✓</span>

                <span>
                  <strong>One step closer</strong>

                  <small>to the support you deserve</small>
                </span>
              </div>
            </div>

            <div className="hero-features">
              <div className="hero-feature">
                <span className="feature-icon" aria-hidden="true">
                  ↗
                </span>

                <span>Discover benefits</span>
              </div>

              <div className="hero-feature">
                <span className="feature-icon" aria-hidden="true">
                  ◎
                </span>

                <span>Track applications</span>
              </div>

              <div className="hero-feature">
                <span className="feature-icon" aria-hidden="true">
                  ♡
                </span>

                <span>Get guidance</span>
              </div>
            </div>

            <p className="hero-footer">
              Built around people. Designed for better access.
            </p>
          </aside>

          {/* RIGHT: LOGIN FORM */}

          <section className="login-panel">
            <div className="login-panel-top">
              <span className="secure-indicator">
                <span />

                SECURE WORKER ACCESS
              </span>

              <span className="login-step">01 / SIGN IN</span>
            </div>

            <div className="login-content">
              <div className="login-heading">
                <p className="login-welcome">WELCOME BACK</p>

                <h2>Good to have you here.</h2>

                <p>
                  Sign in to continue your journey with ShramMitra.
                </p>
              </div>

              <form onSubmit={handleLogin} className="login-form">
                {/* MOBILE NUMBER */}

                <div className="field-group">
                  <label htmlFor="mobile">Mobile number</label>

                  <div className="input-wrap">
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      aria-hidden="true"
                    >
                      <rect
                        x="6"
                        y="2.5"
                        width="12"
                        height="19"
                        rx="2.5"
                        stroke="currentColor"
                        strokeWidth="1.6"
                      />

                      <path
                        d="M10 18.5h4"
                        stroke="currentColor"
                        strokeWidth="1.6"
                        strokeLinecap="round"
                      />
                    </svg>

                    <input
                      id="mobile"
                      type="tel"
                      value={mobile}
                      onChange={(event) =>
                        setMobile(event.target.value)
                      }
                      placeholder="Enter your registered number"
                      minLength={10}
                      maxLength={15}
                      autoComplete="username"
                      inputMode="tel"
                      required
                    />
                  </div>
                </div>

                {/* PASSWORD */}

                <div className="field-group">
                  <div className="password-label-row">
                    <label htmlFor="password">Password</label>
                  </div>

                  <div className="input-wrap">
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      aria-hidden="true"
                    >
                      <rect
                        x="4"
                        y="10"
                        width="16"
                        height="11"
                        rx="2"
                        stroke="currentColor"
                        strokeWidth="1.6"
                      />

                      <path
                        d="M8 10V7a4 4 0 0 1 8 0v3"
                        stroke="currentColor"
                        strokeWidth="1.6"
                        strokeLinecap="round"
                      />
                    </svg>

                    <input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(event) =>
                        setPassword(event.target.value)
                      }
                      placeholder="Enter your password"
                      autoComplete="current-password"
                      required
                    />

                    <button
                      type="button"
                      className="password-toggle"
                      onClick={() =>
                        setShowPassword((visible) => !visible)
                      }
                      aria-label={
                        showPassword
                          ? "Hide password"
                          : "Show password"
                      }
                      aria-pressed={showPassword}
                    >
                      {showPassword ? "Hide" : "Show"}
                    </button>
                  </div>
                </div>

                {/* LOGIN ERROR */}

                {error && (
                  <p className="error-message" role="alert">
                    <span aria-hidden="true">!</span>

                    {error}
                  </p>
                )}

                {/* SUBMIT */}

                <button
                  className="login-submit"
                  type="submit"
                  disabled={loading}
                >
                  <span>
                    {loading
                      ? "Signing you in..."
                      : "Sign in to your account"}
                  </span>

                  {!loading && (
                    <span
                      className="submit-arrow"
                      aria-hidden="true"
                    >
                      →
                    </span>
                  )}
                </button>

                <p className="login-note">
                  By signing in, you can access your benefits and track
                  your applications in one place.
                </p>
              </form>

              <div className="login-divider">
                <span />

                <span>HERE FOR YOU</span>

                <span />
              </div>

              <div className="help-note">
                <span className="help-note-icon" aria-hidden="true">
                  i
                </span>

                <p>
                  Having trouble signing in? Make sure you use the
                  mobile number registered with your account.
                </p>
              </div>
            </div>

            <footer className="login-panel-footer">
              <span>
                © {new Date().getFullYear()} ShramMitra
              </span>

              <span>Access. Awareness. Opportunity.</span>
            </footer>
          </section>
        </section>
      </main>
    );
  }

  // -------------------- WORKER DASHBOARD --------------------

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
            Abhi koi benefit result nahi mila. Worker profile complete
            karo aur check karo ki active schemes ke eligibility rules
            configured hain.
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

                {benefit.status === "Potentially Eligible" && (
                  <p className="muted">
                    Initial rule check match hua hai. Official
                    verification abhi bhi required ho sakti hai.
                  </p>
                )}

                <div className="benefit-reasons">
                  <h4>Why this result?</h4>

                  {benefit.reasons.length > 0 ? (
                    <ul>
                      {benefit.reasons.map((reason, index) => (
                        <li
                          key={`${benefit.scheme_id}-${index}`}
                        >
                          {reason}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="muted">
                      Is result ki detailed explanation available nahi hai.
                    </p>
                  )}
                </div>

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


function App() {
  if (window.location.pathname === "/admin") {
    return <AdminDashboard />;
  }

  return <WorkerApp />;
}

export default App;