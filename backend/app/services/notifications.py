
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        is_read=False,
    )
    db.add(notification)
    return notification


def notify_all_workers(
    db: Session,
    title: str,
    message: str,
    notification_type: str = "SCHEME",
) -> int:
    worker_ids = (
        db.query(User.id)
        .filter(User.role == "WORKER")
        .all()
    )

    for (user_id,) in worker_ids:
        create_notification(
            db=db,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
        )

    return len(worker_ids)
