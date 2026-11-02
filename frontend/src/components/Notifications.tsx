import { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

type Notification = {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
};

type Props = {
  token: string;
};

export default function Notifications({ token }: Props) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadNotifications = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/notifications`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Notifications load nahi ho paayi.");
      }

      const data = await response.json();

      setNotifications(Array.isArray(data) ? data : data.items ?? []);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong."
      );
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId: number) => {
    try {
      const response = await fetch(
        `${API_URL}/notifications/${notificationId}/read`,
        {
          method: "PATCH",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Notification update nahi hui.");
      }

      setNotifications((previous) =>
        previous.map((notification) =>
          notification.id === notificationId
            ? { ...notification, is_read: true }
            : notification
        )
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong."
      );
    }
  };

  useEffect(() => {
    if (token) {
      void loadNotifications();
    }
  }, [token]);

  const unreadCount = notifications.filter(
    (notification) => !notification.is_read
  ).length;

  return (
    <section className="content-section">
      <div className="item-heading">
        <div>
          <h2>Notifications</h2>
          <p className="muted">
            {unreadCount} unread notification{unreadCount !== 1 ? "s" : ""}
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={() => void loadNotifications()}
          disabled={loading}
        >
          Refresh
        </button>
      </div>

      {error && <p className="error-message">{error}</p>}

      {loading ? (
        <p className="muted">Loading notifications...</p>
      ) : notifications.length === 0 ? (
        <div className="empty-state">
          <h3>You're all caught up!</h3>
          <p className="muted">
            Important updates will appear here.
          </p>
        </div>
      ) : (
        <div className="item-list">
          {notifications.map((notification) => (
            <article
              key={notification.id}
              className={`item-card notification-card ${
                notification.is_read ? "notification-read" : "notification-unread"
              }`}
            >
              <div className="item-heading">
                <div>
                  <h3>{notification.title}</h3>
                  <p className="muted">
                    {new Date(notification.created_at).toLocaleString("en-IN")}
                  </p>
                </div>

                {!notification.is_read && (
                  <span className="status-pill">New</span>
                )}
              </div>

              <p>{notification.message}</p>

              {!notification.is_read && (
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => void markAsRead(notification.id)}
                >
                  Mark as read
                </button>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}