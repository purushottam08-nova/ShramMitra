
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

type WorkerDocument = {
  id: number;
  document_type: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  verification_status: string;
  created_at: string;
};

type WorkerProfile = {
  age: number | null;
  monthly_income: number | null;
  epfo_status: boolean | null;
  esic_status: boolean | null;
  nps_status: boolean | null;
  income_tax_payer: boolean | null;
  state: string;
  district: string;
  worker_type: string;
  employment_type: string;
  monthly_income_range: string;
};

const emptyProfile: WorkerProfile = {
  age: null,
  monthly_income: null,
  epfo_status: null,
  esic_status: null,
  nps_status: null,
  income_tax_payer: null,
  state: "",
  district: "",
  worker_type: "",
  employment_type: "",
  monthly_income_range: "",
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
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [benefitsError, setBenefitsError] = useState("");

  const [profile, setProfile] = useState<WorkerProfile>(emptyProfile);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMessage, setProfileMessage] = useState("");
  const [profileError, setProfileError] = useState("");

  const [documents, setDocuments] = useState<WorkerDocument[]>([]);
  const [documentType, setDocumentType] = useState("Aadhaar Card");
  const [documentFile, setDocumentFile] = useState<File | null>(null);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [documentUploading, setDocumentUploading] = useState(false);
  const [documentError, setDocumentError] = useState("");
  const [documentMessage, setDocumentMessage] = useState("");
  
  // -------------------- LOGIN --------------------

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setBenefitsError("");
    setProfileError("");
    setProfileMessage("");

    try {
      // 1. Login request
      const loginResponse = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          mobile: mobile.trim(),
          password,
        }),
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

      // 2. User, dashboard aur profile parallel mein load karo
      const [
        userResponse,
        dashboardResponse,
        profileResponse,
      ] = await Promise.all([
        fetch(`${API_URL}/auth/me`, { headers }),
        fetch(`${API_URL}/dashboard/me`, { headers }),
        fetch(`${API_URL}/profile/me`, { headers }),
      ]);

      // 3. Session validation
      if (
        userResponse.status === 401 ||
        dashboardResponse.status === 401 ||
        profileResponse.status === 401
      ) {
        throw new Error(
          "Session validate nahi hua. Dobara login karo.",
        );
      }

      if (
        !userResponse.ok ||
        !dashboardResponse.ok ||
        !profileResponse.ok
      ) {
        throw new Error(
          "User, dashboard ya profile load nahi hua. Dobara try karo.",
        );
      }

      // 4. Response data
      const userData: User = await userResponse.json();

      const dashboardData: DashboardData =
        await dashboardResponse.json();

      const profileData: WorkerProfile =
        await profileResponse.json();

      // 5. Main application state
      setToken(loginData.access_token);
      setUser(userData);
      setDashboard(dashboardData);

      setProfile({
        ...emptyProfile,
        ...profileData,
      });

      // 6. Benefits fetch
      // Benefits API fail hone par bhi dashboard accessible rahega.
      try {
        const benefitsResponse = await fetch(
          `${API_URL}/benefits/me`,
          { headers },
        );

        if (!benefitsResponse.ok) {
          throw new Error(
            "Benefits API ne error return kiya.",
          );
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

      // 7. Document Vault fetch
      try {
        const documentsResponse = await fetch(
          `${API_URL}/documents`,
          {
            headers: {
              Authorization: `Bearer ${loginData.access_token}`,
            },
          },
        );

        if (!documentsResponse.ok) {
          throw new Error("Documents load nahi ho paaye.");
        }

        const documentsData: WorkerDocument[] =
          await documentsResponse.json();

        setDocuments(documentsData);
      } catch {
        setDocuments([]);
        setDocumentError(
          "Document Vault load nahi ho paya. Retry karo.",
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


  // -------------------- REFRESH DASHBOARD --------------------

  async function handleRefresh() {
    if (!token) return;

    setRefreshing(true);
    setError("");
    setBenefitsError("");

    const headers = {
      Authorization: `Bearer ${token}`,
    };

    try {
      const [dashboardResponse, benefitsResponse] = await Promise.all([
        fetch(`${API_URL}/dashboard/me`, { headers }),
        fetch(`${API_URL}/benefits/me`, { headers }),
      ]);
  
      if (
        dashboardResponse.status === 401 ||
        benefitsResponse.status === 401
      ) {
        throw new Error("Session expire ho gaya. Dobara login karo.");
      }

      if (!dashboardResponse.ok) {
        throw new Error("Dashboard refresh nahi ho paya.");
      }

      const dashboardData: DashboardData =
        await dashboardResponse.json();

      setDashboard(dashboardData);

      if (!benefitsResponse.ok) {
        setBenefitsError(
          "Benefits refresh nahi ho paaye. Thodi der baad retry karo.",
        );
      } else {
        const benefitsData: Benefit[] =
          await benefitsResponse.json();

        setBenefits(benefitsData);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Dashboard refresh karte waqt problem hui.",
      );
    } finally {
      setRefreshing(false);
    }
  }


  async function handleProfileSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!token) return;

    setProfileSaving(true);
    setProfileMessage("");
    setProfileError("");

    try {
    const response = await fetch(`${API_URL}/profile/me`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(profile),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);

      throw new Error(
        errorData?.detail || "Profile update nahi ho paya.",
      );
    }

    const updatedProfile: WorkerProfile = await response.json();

    setProfile({
      ...emptyProfile,
      ...updatedProfile,
    });

    setProfileMessage("Profile successfully update ho gaya!");

    // Updated profile ke basis par benefits refresh karo.
    const benefitsResponse = await fetch(`${API_URL}/benefits/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (benefitsResponse.ok) {
      const updatedBenefits: Benefit[] =
        await benefitsResponse.json();

      setBenefits(updatedBenefits);
    }
    } catch (err) {
    setProfileError(
      err instanceof Error
        ? err.message
        : "Profile update karte waqt error aaya.",
    );
    } finally {
    setProfileSaving(false);
    }
  }

  async function loadDocuments() {
    if (!token) return;

    setDocumentsLoading(true);
    setDocumentError("");

    try {
      const response = await fetch(`${API_URL}/documents`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Documents load nahi ho paaye.");
      }

      const data: WorkerDocument[] = await response.json();
      setDocuments(data);
    } catch (err) {
      setDocumentError(
        err instanceof Error
          ? err.message
          : "Documents load karte waqt error aaya.",
      );
    } finally {
      setDocumentsLoading(false);
    }
  }

  async function handleDocumentUpload(  
  event: FormEvent<HTMLFormElement>,
) {
  event.preventDefault();

  if (!token || !documentFile) {
    setDocumentError("Pehle ek file select karo.");
    return;
  }

  if (documentFile.size > 5 * 1024 * 1024) {
    setDocumentError("File size 5 MB se kam honi chahiye.");
    return;
  }

  setDocumentUploading(true);
  setDocumentError("");
  setDocumentMessage("");

  try {
    const formData = new FormData();

    formData.append("document_type", documentType);
    formData.append("file", documentFile);

    const response = await fetch(`${API_URL}/documents/upload`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    const responseData = await response.json().catch(() => null);

    if (!response.ok) {
      throw new Error(
        responseData?.detail || "Document upload nahi ho paya.",
      );
    }

    setDocumentMessage("Document successfully upload ho gaya!");
    setDocumentFile(null);

    const fileInput = document.getElementById(
      "document-file",
    ) as HTMLInputElement | null;

    if (fileInput) {
      fileInput.value = "";
    }

    await loadDocuments();
  } catch (err) {
    setDocumentError(
      err instanceof Error
        ? err.message
        : "Upload karte waqt error aaya.",
    );
  } finally {
    setDocumentUploading(false);
  }
  }

  async function handleDocumentDownload(documentId: number) {
    if (!token) return;

    setDocumentError("");

    try {
      const response = await fetch(
        `${API_URL}/documents/${documentId}/download`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (!response.ok) {
        throw new Error("Document download nahi ho paya.");
      }

      const blob = await response.blob();
      const downloadUrl = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download =
        documents.find((document) => document.id === documentId)
          ?.original_filename || "document";

      document.body.appendChild(link);
      link.click();
      link.remove();

      URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      setDocumentError(
        err instanceof Error
          ? err.message
          : "Download karte waqt error aaya.",
      );
    }
  }

  async function handleDocumentDelete(documentId: number) {
    if (!token) return;

    const confirmed = window.confirm(
      "Kya tum ye document permanently delete karna chahte ho?",
    );

    if (!confirmed) return;

    setDocumentError("");
    setDocumentMessage("");

    try {
      const response = await fetch(
        `${API_URL}/documents/${documentId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      const responseData = await response.json().catch(() => null);
  
      if (!response.ok) {
        throw new Error(
          responseData?.detail || "Document delete nahi ho paya.",
        );
      }

      setDocumentMessage("Document successfully delete ho gaya!");

      await loadDocuments();
    } catch (err) {
      setDocumentError(
        err instanceof Error
          ? err.message
          : "Delete karte waqt error aaya.",
      );
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

        <div className="dashboard-header-actions">
          <button
            className="secondary-button"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshing ? "Refreshing..." : "↻ Refresh"}
          </button>

          <button
            className="secondary-button"
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>
      </header>

      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}

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

      <section className="content-section">
        <h2>Your worker profile</h2>

        <p className="muted">
          Apni details updated rakho taaki relevant schemes check ho sakein.
        </p>

        <form className="profile-form" onSubmit={handleProfileSave}>
          <div className="profile-fields">
            <label>
              Age
              <input
                type="number"
                min="18"
                max="100"
                value={profile.age ?? ""}
                onChange={(event) =>
                  setProfile({
                    ...profile,
                    age: event.target.value
                      ? Number(event.target.value)
                      : null,
                  })
                }
              />
            </label>

            <label>
              Monthly income (₹)
              <input
                type="number"
                min="0"
                value={profile.monthly_income ?? ""}
                onChange={(event) =>
                  setProfile({
                    ...profile,
                    monthly_income: event.target.value
                      ? Number(event.target.value)
                      : null,
                  })
                }
              />
            </label>

            <label>
              State
              <input
                value={profile.state}
                onChange={(event) =>
                  setProfile({ ...profile, state: event.target.value })
                }
                placeholder="e.g. Maharashtra"
              />
            </label>

            <label>
              District
              <input
                value={profile.district}
                onChange={(event) =>
                  setProfile({ ...profile, district: event.target.value })
                }
                placeholder="e.g. Nashik"
              />
            </label>

            <label>
              Worker type
              <input
                value={profile.worker_type}
                onChange={(event) =>
                  setProfile({
                    ...profile,
                    worker_type: event.target.value,
                  })
                }
                placeholder="e.g. Delivery Partner"
              />
            </label>

            <label>
              Employment type
              <input
                value={profile.employment_type}
                onChange={(event) =>
                  setProfile({
                    ...profile,
                    employment_type: event.target.value,
                  })
                }
                placeholder="e.g. Self-employed"
              />
            </label>

            <label>
              Monthly income range
              <input
                value={profile.monthly_income_range}
                onChange={(event) =>
                  setProfile({
                    ...profile,
                    monthly_income_range: event.target.value,
                  })
                }
                placeholder="e.g. 10000-20000"
              />
            </label>
          </div>

          <div className="profile-fields">
            {(
              [
                ["epfo_status", "EPFO registered?"],
                ["esic_status", "ESIC registered?"],
                ["nps_status", "NPS registered?"],
                ["income_tax_payer", "Income tax payer?"],
              ] as const
            ).map(([field, label]) => (
              <label key={field}>
                {label}
                <select
                  value={
                    profile[field] === null
                      ? ""
                      : profile[field]
                        ? "true"
                        : "false"
                  }
                  onChange={(event) =>
                    setProfile({
                      ...profile,
                      [field]:
                        event.target.value === ""
                          ? null
                          : event.target.value === "true",
                    })
                  }
                >
                  <option value="">Not sure / Not provided</option>
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </label>
            ))}
          </div>

          {profileError && (
            <p className="error-message" role="alert">
              {profileError}
            </p>
          )}

          {profileMessage && (
            <p className="profile-success" role="status">
              {profileMessage}
            </p>
          )}

          <button
            className="login-submit"
            type="submit"
            disabled={profileSaving}
          >
            {profileSaving ? "Saving profile..." : "Save profile"}
          </button>
        </form>
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

      {/* DOCUMENT VAULT */}

      <section className="content-section">
        <div className="item-heading">
          <div>
            <h2>Document Vault</h2>
            <p className="muted">
              Apne important documents securely manage karo.
            </p>
          </div>

          <button
            className="secondary-button"
            type="button"
            onClick={loadDocuments}
            disabled={documentsLoading}
          >
            {documentsLoading ? "Loading..." : "↻ Refresh"}
          </button>
        </div>

        <form
          className="profile-form"
          onSubmit={handleDocumentUpload}
        >
          <div className="profile-fields">
            <label>
              Document type
      
              <select
                value={documentType}
                onChange={(event) =>
                  setDocumentType(event.target.value)
                }
              >
                <option value="Aadhaar Card">Aadhaar Card</option>
                <option value="PAN Card">PAN Card</option>
                <option value="Bank Passbook">Bank Passbook</option>
                <option value="Driving License">Driving License</option>
                <option value="Ration Card">Ration Card</option>
                <option value="Income Certificate">Income Certificate</option>
                <option value="Other">Other</option>
              </select>
            </label>

            <label>
              Select document

              <input
                id="document-file"
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={(event) =>
                  setDocumentFile(
                    event.target.files?.[0] || null,
                  )
                }
                required
              />
            </label>
          </div>

          <p className="muted">
            Accepted formats: PDF, JPG, PNG. Maximum size: 5 MB.
          </p>

          {documentError && (
            <p className="error-message" role="alert">
              {documentError}
            </p>
          )}

          {documentMessage && (
            <p className="profile-success" role="status">
              {documentMessage}
            </p>
          )}

          <button
            className="login-submit"
            type="submit"
            disabled={documentUploading || !documentFile}
          >
            {documentUploading
              ? "Uploading document..."
              : "Upload document"}
          </button>
        </form>

        <div className="item-list">
          {documentsLoading ? (
            <p className="empty-state">
              Documents load ho rahe hain...
            </p>
          ) : documents.length === 0 ? (
            <p className="empty-state">
              Abhi koi document upload nahi hua.
            </p>
          ) : (
            documents.map((document) => (
              <article
                className="item-card"
                key={document.id}
              >
                <div className="item-heading">
                  <h3>{document.document_type}</h3>
      
                  <span className="status-pill">
                    {document.verification_status}
                  </span>
                </div>

                <p>{document.original_filename}</p>
      
                <p className="muted">
                  {(document.file_size / 1024).toFixed(1)} KB
                  {" · "}
                  {new Date(document.created_at).toLocaleDateString()}
                </p>

                <div className="dashboard-header-actions">
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() =>
                      handleDocumentDownload(document.id)
                    }
                  >
                    Download
                  </button>

                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() =>
                      handleDocumentDelete(document.id)
                    }
                  >
                    Delete
                  </button>
                </div>
              </article>
            ))
          )}
        </div>
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
