import { useEffect, useMemo, useState, type FormEvent } from "react";
import "./AdminDashboard.css";

const API_URL = "http://127.0.0.1:8000";

type Scheme = {
  id: number;
  name: string;
  verification_status?: string;
  version?: string | null;
  source_url?: string | null;
};

type HistoryItem = {
  id: number;
  verifier_id: number;
  verifier_name: string;
  previous_status: string | null;
  new_status: string;
  source_url: string;
  version: string;
  notes: string | null;
  verified_at: string;
};

type HistoryResponse = {
  scheme_id: number;
  scheme_name: string;
  total_records: number;
  history: HistoryItem[];
};

function AdminDashboard() {
  const [mobile, setMobile] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState<string | null>(null);

  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [selectedScheme, setSelectedScheme] = useState<Scheme | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  const [sourceUrl, setSourceUrl] = useState("");
  const [version, setVersion] = useState("");
  const [notes, setNotes] = useState("");
  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const filteredSchemes = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) return schemes;

    return schemes.filter((scheme) =>
      scheme.name.toLowerCase().includes(query),
    );
  }, [schemes, search]);

  async function apiRequest(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });

    if (response.status === 401) {
      throw new Error("Session invalid hai. Dobara login karo.");
    }

    if (response.status === 403) {
      throw new Error("Admin access required. Ye account ADMIN nahi hai.");
    }

    if (!response.ok) {
      const data = await response.json().catch(() => null);
      throw new Error(data?.detail || "Request failed.");
    }

    return response.json();
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mobile, password }),
      });

      if (!response.ok) {
        throw new Error("Mobile number ya password galat hai.");
      }

      const data = await response.json();

      setToken(data.access_token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  async function loadSchemes() {
    setError("");

    try {
      const data: Scheme[] = await apiRequest("/schemes");
      setSchemes(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Schemes load nahi hui.");
    }
  }

  async function loadHistory(scheme: Scheme) {
    setSelectedScheme(scheme);
    setHistory([]);
    setError("");
    setMessage("");
    setLoading(true);

    try {
      const data: HistoryResponse = await apiRequest(
        `/admin/schemes/${scheme.id}/verification-history`,
      );

      setHistory(data.history);
      setSelectedScheme({
        ...scheme,
        name: data.scheme_name,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "History load nahi hui.");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedScheme) return;

    setLoading(true);
    setError("");
    setMessage("");

    try {
      await apiRequest(`/admin/schemes/${selectedScheme.id}/verify`, {
        method: "POST",
        body: JSON.stringify({
          source_url: sourceUrl,
          version,
          notes,
        }),
      });

      setMessage("Scheme verified successfully!");

      await loadHistory(selectedScheme);

      setSourceUrl("");
      setVersion("");
      setNotes("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed.");
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    setToken(null);
    setSchemes([]);
    setSelectedScheme(null);
    setHistory([]);
    setPassword("");
    setSearch("");
    setError("");
    setMessage("");
  }

  useEffect(() => {
    if (token) {
      loadSchemes();
    }
  }, [token]);

  if (!token) {
    return (
      <main className="admin-login-page">
        <form className="admin-login-card" onSubmit={handleLogin}>
          <div className="admin-brand">
            <span className="admin-brand-symbol">S</span>
            <span>ShramMitra</span>
          </div>

          <p className="admin-eyebrow">ADMINISTRATION</p>

          <h1>Welcome back.</h1>

          <p className="admin-subtitle">
            Sign in to manage scheme verification and maintain trusted
            government benefit information.
          </p>

          {error && (
            <div className="admin-error" role="alert">
              {error}
            </div>
          )}

          <label>
            Mobile number
            <input
              value={mobile}
              onChange={(event) => setMobile(event.target.value)}
              required
              inputMode="numeric"
              autoComplete="username"
              placeholder="Enter mobile number"
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              autoComplete="current-password"
              placeholder="Enter password"
            />
          </label>

          <button className="admin-primary-button" disabled={loading}>
            {loading ? "Signing in..." : "Sign in to workspace"}
            {!loading && <span>→</span>}
          </button>

          <a className="admin-worker-link" href="/">
            ← Back to Worker Portal
          </a>

          <div className="admin-login-footer">
            <span>SECURE ADMIN ACCESS</span>
            <span>© {new Date().getFullYear()} ShramMitra</span>
          </div>
        </form>
      </main>
    );
  }

  return (
    <main className="admin-app">
      <aside className="admin-sidebar">
        <a href="/admin" className="admin-sidebar-brand">
          <span className="admin-brand-symbol">S</span>

          <span>
            <strong>ShramMitra</strong>
            <small>ADMIN CONSOLE</small>
          </span>
        </a>

        <div className="admin-sidebar-section">
          <p className="admin-sidebar-label">WORKSPACE</p>

          <a href="#overview" className="admin-nav-item active">
            <span className="admin-nav-icon">⌂</span>
            Overview
          </a>

          <a href="#schemes" className="admin-nav-item">
            <span className="admin-nav-icon">▤</span>
            Scheme management
          </a>

          <a href="#verification" className="admin-nav-item">
            <span className="admin-nav-icon">✓</span>
            Verification history
          </a>
        </div>

        <div className="admin-sidebar-bottom">
          <div className="admin-sidebar-help">
            <span className="admin-help-icon">i</span>

            <div>
              <strong>Need assistance?</strong>
              <p>Keep scheme information accurate and up to date.</p>
            </div>
          </div>

          <button className="admin-sidebar-logout" onClick={handleLogout}>
            <span>↪</span>
            Logout
          </button>
        </div>
      </aside>

      <section className="admin-main">
        <header className="admin-topbar">
          <div>
            <span className="admin-breadcrumb">Workspace / Overview</span>
            <p>Scheme verification workspace</p>
          </div>

          <div className="admin-topbar-right">
            <span className="admin-live-indicator">
              <span />
              System operational
            </span>

            <div className="admin-avatar">A</div>
          </div>
        </header>

        <div className="admin-content">
          <section className="admin-welcome" id="overview">
            <div>
              <p className="admin-eyebrow">ADMIN WORKSPACE</p>

              <h1>Scheme verification</h1>

              <p>
                Review, verify and maintain trusted information about
                government benefit schemes.
              </p>
            </div>

            <button
              className="admin-refresh-button"
              onClick={loadSchemes}
              disabled={loading}
            >
              <span>↻</span>
              Refresh data
            </button>
          </section>

          {error && (
            <div className="admin-error" role="alert">
              {error}
            </div>
          )}

          {message && (
            <div className="admin-success" role="status">
              {message}
            </div>
          )}

          <section className="admin-overview-grid">
            <article className="admin-overview-card">
              <div className="admin-overview-top">
                <span className="admin-overview-icon green">▤</span>
                <span className="admin-overview-label">Active schemes</span>
              </div>

              <strong>{schemes.length}</strong>

              <p>Available in the worker portal</p>
            </article>

            <article className="admin-overview-card">
              <div className="admin-overview-top">
                <span className="admin-overview-icon blue">✓</span>
                <span className="admin-overview-label">
                  Verification records
                </span>
              </div>

              <strong>{history.length}</strong>

              <p>
                {selectedScheme
                  ? `For ${selectedScheme.name}`
                  : "Select a scheme to view records"}
              </p>
            </article>

            <article className="admin-overview-card">
              <div className="admin-overview-top">
                <span className="admin-overview-icon amber">◷</span>
                <span className="admin-overview-label">Selected scheme</span>
              </div>

              <strong className="admin-selected-number">
                {selectedScheme ? `#${selectedScheme.id}` : "—"}
              </strong>

              <p>
                {selectedScheme
                  ? "Ready for verification"
                  : "No scheme selected"}
              </p>
            </article>
          </section>

          <section className="admin-workspace-grid">
            <section className="admin-panel" id="schemes">
              <div className="admin-panel-heading">
                <div>
                  <p className="admin-eyebrow">SCHEME DIRECTORY</p>
                  <h2>Available schemes</h2>
                  <p className="admin-panel-description">
                    Select a scheme to review its verification details.
                  </p>
                </div>

                <span className="admin-total-badge">
                  {schemes.length} total
                </span>
              </div>

              <div className="admin-search">
                <span>⌕</span>

                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search schemes..."
                  aria-label="Search schemes"
                />

                {search && (
                  <button
                    onClick={() => setSearch("")}
                    aria-label="Clear search"
                  >
                    ×
                  </button>
                )}
              </div>

              <div className="admin-scheme-list">
                {filteredSchemes.length === 0 ? (
                  <div className="admin-empty">
                    <span>⌕</span>
                    <p>No schemes found.</p>
                  </div>
                ) : (
                  filteredSchemes.map((scheme) => (
                    <button
                      className={`admin-scheme-item ${
                        selectedScheme?.id === scheme.id ? "selected" : ""
                      }`}
                      key={scheme.id}
                      onClick={() => loadHistory(scheme)}
                    >
                      <span className="admin-scheme-symbol">S</span>

                      <span className="admin-scheme-info">
                        <strong>{scheme.name}</strong>
                        <small>Scheme ID: {scheme.id}</small>
                      </span>

                      <span className="admin-arrow">→</span>
                    </button>
                  ))
                )}
              </div>
            </section>

            <section className="admin-panel admin-detail-panel">
              {!selectedScheme ? (
                <div className="admin-empty-large">
                  <span className="admin-empty-icon">↗</span>

                  <h2>Select a scheme</h2>

                  <p>
                    Choose a scheme from the directory to view its
                    verification history and manage verification.
                  </p>
                </div>
              ) : (
                <>
                  <div className="admin-panel-heading">
                    <div>
                      <p className="admin-eyebrow">SELECTED SCHEME</p>
                      <h2>{selectedScheme.name}</h2>
                    </div>

                    <span className="admin-total-badge">
                      {history.length} records
                    </span>
                  </div>

                  <div className="admin-scheme-meta">
                    <div>
                      <span>Scheme ID</span>
                      <strong>#{selectedScheme.id}</strong>
                    </div>

                    <div>
                      <span>Latest version</span>
                      <strong>
                        {history[0]?.version || selectedScheme.version || "—"}
                      </strong>
                    </div>

                    <div>
                      <span>Verification status</span>
                      <strong className="admin-status-text">
                        {history[0]?.new_status ||
                          selectedScheme.verification_status ||
                          "Unverified"}
                      </strong>
                    </div>
                  </div>

                  <section className="admin-history-section" id="verification">
                    <div className="admin-section-heading">
                      <div>
                        <h3>Verification history</h3>
                        <p>Record of previous scheme verification activity.</p>
                      </div>
                    </div>

                    {loading ? (
                      <div className="admin-empty">
                        <p>Loading verification history...</p>
                      </div>
                    ) : history.length === 0 ? (
                      <div className="admin-history-empty">
                        <span>◷</span>
                        <strong>No verification records yet</strong>
                        <p>
                          Verify this scheme to create its first record.
                        </p>
                      </div>
                    ) : (
                      <div className="admin-timeline">
                        {history.map((item) => (
                          <article
                            className="admin-timeline-item"
                            key={item.id}
                          >
                            <span className="admin-timeline-dot" />

                            <div className="admin-history-card">
                              <div className="admin-history-top">
                                <span className="admin-verified-pill">
                                  {item.new_status}
                                </span>

                                <time>
                                  {new Date(
                                    item.verified_at,
                                  ).toLocaleString()}
                                </time>
                              </div>

                              <h4>
                                {item.previous_status || "UNVERIFIED"}
                                <span> → </span>
                                {item.new_status}
                              </h4>

                              <p>
                                <strong>Verified by:</strong>{" "}
                                {item.verifier_name}
                              </p>

                              <p>
                                <strong>Version:</strong> {item.version}
                              </p>

                              <p className="admin-source-row">
                                <strong>Official source:</strong>{" "}
                                <a
                                  href={item.source_url}
                                  target="_blank"
                                  rel="noreferrer"
                                >
                                  Open source ↗
                                </a>
                              </p>

                              {item.notes && (
                                <p>
                                  <strong>Notes:</strong> {item.notes}
                                </p>
                              )}
                            </div>
                          </article>
                        ))}
                      </div>
                    )}
                  </section>

                  <form
                    className="admin-verify-form"
                    onSubmit={handleVerify}
                  >
                    <div className="admin-section-heading">
                      <div>
                        <p className="admin-eyebrow">VERIFICATION ACTION</p>
                        <h3>Verify this scheme</h3>
                        <p>
                          Add the official source and verification details.
                        </p>
                      </div>
                    </div>

                    <label>
                      Official source URL
                      <input
                        type="url"
                        value={sourceUrl}
                        onChange={(event) =>
                          setSourceUrl(event.target.value)
                        }
                        placeholder="https://official.gov.in"
                        required
                      />
                    </label>

                    <label>
                      Version
                      <input
                        value={version}
                        onChange={(event) => setVersion(event.target.value)}
                        placeholder="e.g. 1.0"
                        required
                      />
                    </label>

                    <label>
                      Verification notes
                      <textarea
                        value={notes}
                        onChange={(event) => setNotes(event.target.value)}
                        placeholder="Describe what you verified..."
                        rows={3}
                      />
                    </label>

                    <button
                      className="admin-primary-button"
                      disabled={loading}
                    >
                      {loading ? "Processing..." : "Verify scheme"}
                      {!loading && <span>→</span>}
                    </button>
                  </form>
                </>
              )}
            </section>
          </section>

          <footer className="admin-footer">
            <span>© {new Date().getFullYear()} ShramMitra</span>
            <span>From access to opportunity.</span>
          </footer>
        </div>
      </section>
    </main>
  );
}

export default AdminDashboard;