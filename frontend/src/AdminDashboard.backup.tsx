
import { useEffect, useState, type FormEvent } from "react";
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

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function apiRequest(
    endpoint: string,
    options: RequestInit = {},
  ) {
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
          <div className="admin-brand">ShramMitra</div>
          <p className="admin-eyebrow">ADMINISTRATION</p>
          <h1>Admin Login</h1>
          <p className="admin-subtitle">
            Sign in to manage scheme verification.
          </p>

          {error && <div className="admin-error">{error}</div>}

          <label>
            Mobile number
            <input
              value={mobile}
              onChange={(event) => setMobile(event.target.value)}
              required
              inputMode="numeric"
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
              placeholder="Enter password"
            />
          </label>

          <button disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </button>

          <a className="admin-worker-link" href="/">
            Back to Worker Portal
          </a>
        </form>
      </main>
    );
  }

  return (
    <main className="admin-page">
      <header className="admin-header">
        <div>
          <div className="admin-brand">ShramMitra</div>
          <p>Scheme Verification Console</p>
        </div>

        <button className="admin-logout" onClick={handleLogout}>
          Logout
        </button>
      </header>

      <section className="admin-content">
        <div className="admin-page-heading">
          <div>
            <p className="admin-eyebrow">ADMIN WORKSPACE</p>
            <h1>Scheme Verification</h1>
            <p>Review schemes and maintain verification history.</p>
          </div>

          <div className="admin-stat">
            <span>Active schemes</span>
            <strong>{schemes.length}</strong>
          </div>
        </div>

        {error && <div className="admin-error">{error}</div>}
        {message && <div className="admin-success">{message}</div>}

        <div className="admin-layout">
          <section className="admin-panel">
            <div className="admin-panel-heading">
              <h2>Available schemes</h2>
              <button
                className="admin-refresh"
                onClick={loadSchemes}
                disabled={loading}
              >
                Refresh
              </button>
            </div>

            {schemes.length === 0 ? (
              <p className="admin-empty">No active schemes found.</p>
            ) : (
              <div className="admin-scheme-list">
                {schemes.map((scheme) => (
                  <button
                    className={`admin-scheme-item ${
                      selectedScheme?.id === scheme.id ? "selected" : ""
                    }`}
                    key={scheme.id}
                    onClick={() => loadHistory(scheme)}
                  >
                    <span>
                      <strong>{scheme.name}</strong>
                      <small>Scheme ID: {scheme.id}</small>
                    </span>

                    <span className="admin-arrow">→</span>
                  </button>
                ))}
              </div>
            )}
          </section>

          <section className="admin-panel admin-history-panel">
            {!selectedScheme ? (
              <div className="admin-empty-large">
                <span>↗</span>
                <h2>Select a scheme</h2>
                <p>
                  Choose a scheme from the list to view its verification
                  history.
                </p>
              </div>
            ) : (
              <>
                <div className="admin-panel-heading">
                  <div>
                    <p className="admin-eyebrow">SELECTED SCHEME</p>
                    <h2>{selectedScheme.name}</h2>
                  </div>

                  <span className="admin-count">
                    {history.length} records
                  </span>
                </div>

                <div className="admin-history-list">
                  {history.length === 0 ? (
                    <p className="admin-empty">
                      No verification history available yet.
                    </p>
                  ) : (
                    history.map((item) => (
                      <article className="admin-history-item" key={item.id}>
                        <div className="admin-history-top">
                          <span className="admin-verified-pill">
                            {item.new_status}
                          </span>
                          <time>
                            {new Date(item.verified_at).toLocaleString()}
                          </time>
                        </div>

                        <h3>
                          {item.previous_status || "UNVERIFIED"}{" "}
                          <span>→</span> {item.new_status}
                        </h3>

                        <p>
                          <strong>Verified by:</strong> {item.verifier_name}
                        </p>

                        <p>
                          <strong>Version:</strong> {item.version}
                        </p>

                        <p>
                          <strong>Source:</strong>{" "}
                          <a
                            href={item.source_url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Open official source ↗
                          </a>
                        </p>

                        {item.notes && (
                          <p>
                            <strong>Notes:</strong> {item.notes}
                          </p>
                        )}
                      </article>
                    ))
                  )}
                </div>

                <form className="admin-verify-form" onSubmit={handleVerify}>
                  <h3>Verify this scheme</h3>

                  <label>
                    Official source URL
                    <input
                      type="url"
                      value={sourceUrl}
                      onChange={(event) => setSourceUrl(event.target.value)}
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
                      placeholder="What did you verify?"
                      rows={3}
                    />
                  </label>

                  <button disabled={loading}>
                    {loading ? "Processing..." : "Verify scheme"}
                  </button>
                </form>
              </>
            )}
          </section>
        </div>
      </section>
    </main>
  );
}

export default AdminDashboard;
