import { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

type Application = {
  id: number;
  scheme_name: string;
  application_number?: string | null;
  status: string;
  applied_at?: string | null;
  updated_at?: string | null;
  next_action?: string | null;
};

type ApplicationHistory = {
  id: number;
  status: string;
  note?: string | null;
  changed_at: string;
};

type Props = {
  token: string;
};

const formatDate = (value?: string | null) => {
  if (!value) return "Not available";

  return new Date(value).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
};

const formatStatus = (status: string) =>
  status.replaceAll("_", " ").toLowerCase();

export default function ApplicationTracking({ token }: Props) {
  const [applications, setApplications] = useState<Application[]>([]);
  const [history, setHistory] = useState<Record<number, ApplicationHistory[]>>(
    {}
  );
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState<number | null>(null);
  const [error, setError] = useState("");

  const loadApplications = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/applications/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Applications load nahi ho paayi.");
      }

      const data = await response.json();

      setApplications(Array.isArray(data) ? data : data.items ?? []);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong."
      );
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async (applicationId: number) => {
    setHistoryLoading(applicationId);

    try {
      const response = await fetch(
        `${API_URL}/applications/${applicationId}/history`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Application history load nahi hui.");
      }

      const data = await response.json();

      setHistory((previous) => ({
        ...previous,
        [applicationId]: Array.isArray(data) ? data : data.items ?? [],
      }));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "History load nahi hui."
      );
    } finally {
      setHistoryLoading(null);
    }
  };

  const toggleHistory = async (applicationId: number) => {
    if (expandedId === applicationId) {
      setExpandedId(null);
      return;
    }

    setExpandedId(applicationId);

    if (!history[applicationId]) {
      await loadHistory(applicationId);
    }
  };

  useEffect(() => {
    if (token) {
      void loadApplications();
    }
  }, [token]);

  if (loading) {
    return (
      <section className="content-section">
        <p className="muted">Loading applications...</p>
      </section>
    );
  }

  return (
    <section className="content-section">
      <div className="item-heading">
        <div>
          <h2>Application Tracking</h2>
          <p className="muted">
            Track your applications and see what to do next.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={() => void loadApplications()}
        >
          Refresh
        </button>
      </div>

      {error && <p className="error-message">{error}</p>}

      {applications.length === 0 ? (
        <div className="empty-state">
          <h3>No applications yet</h3>
          <p className="muted">
            Your scheme applications will appear here after you apply.
          </p>
        </div>
      ) : (
        <div className="item-list">
          {applications.map((application) => {
            const isExpanded = expandedId === application.id;

            return (
              <article className="item-card" key={application.id}>
                <div className="item-heading">
                  <div>
                    <h3>{application.scheme_name}</h3>
                    <p className="muted">
                      Reference:{" "}
                      {application.application_number || application.id}
                    </p>
                  </div>

                  <span className="status-pill">
                    {formatStatus(application.status)}
                  </span>
                </div>

                <div className="application-meta">
                  <p className="muted">
                    Applied: {formatDate(application.applied_at)}
                  </p>

                  <p className="muted">
                    Last updated: {formatDate(application.updated_at)}
                  </p>
                </div>

                <div className="application-next-action">
                  <strong>Next action</strong>

                  <p>
                    {application.next_action ||
                      (application.status.toLowerCase() === "approved"
                        ? "Your application has been approved. Check the official portal for benefit details."
                        : application.status.toLowerCase() === "rejected"
                          ? "Check the rejection reason on the official portal. Contact the relevant department if needed."
                          : "Check the official portal for updates and any pending documents or verification.")}
                  </p>
                </div>

                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => void toggleHistory(application.id)}
                >
                  {isExpanded ? "Hide status history" : "View status history"}
                </button>

                {isExpanded && (
                  <div className="application-history">
                    <h4>Status history</h4>

                    {historyLoading === application.id ? (
                      <p className="muted">Loading history...</p>
                    ) : history[application.id]?.length ? (
                      <ol className="application-timeline">
                        {history[application.id].map((entry) => (
                          <li key={entry.id}>
                            <strong>{formatStatus(entry.status)}</strong>

                            <p className="muted">
                              {formatDate(entry.changed_at)}
                            </p>

                            {entry.note && <p>{entry.note}</p>}
                          </li>
                        ))}
                      </ol>
                    ) : (
                      <p className="muted">
                        No status history is available yet.
                      </p>
                    )}
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}