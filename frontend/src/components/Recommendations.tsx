import { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

type Recommendation = {
  scheme_id: number;
  scheme_name: string;
  description: string;
  reasons: string[];
  eligibility_status: string;
};

type Props = {
  token: string | null;
};

export default function Recommendations({ token }: Props) {
  const [items, setItems] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadRecommendations = async () => {
      try {
        const response = await fetch(`${API_URL}/recommendations/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error("Recommendations load nahi ho paayi.");
        }

        const data = await response.json();
        setItems(data.recommendations ?? []);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Something went wrong."
        );
      } finally {
        setLoading(false);
      }
    };

    if (token) void loadRecommendations();
  }, [token]);

  return (
    <section className="content-section">
      <div className="item-heading">
        <div>
          <h2>Recommended for You</h2>
          <p className="muted">
            Schemes that may match your profile.
          </p>
        </div>
      </div>

      {loading && <p className="muted">Finding relevant schemes...</p>}

      {error && <p className="error-message">{error}</p>}

      {!loading && !error && items.length === 0 && (
        <div className="empty-state">
          <h3>No recommendations yet</h3>
          <p className="muted">
            Complete your profile to discover potentially relevant schemes.
          </p>
        </div>
      )}

      <div className="item-list">
        {items.map((item) => (
          <article className="item-card" key={item.scheme_id}>
            <div className="item-heading">
              <h3>{item.scheme_name}</h3>
              <span className="status-pill">Potential match</span>
            </div>

            <p>{item.description}</p>

            <strong>Why this may match you:</strong>

            <ul>
              {item.reasons.map((reason, index) => (
                <li key={index}>{reason}</li>
              ))}
            </ul>

            <p className="muted">
              This is an initial profile match, not a confirmed eligibility
              decision. Check the scheme's official eligibility rules before
              applying.
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}