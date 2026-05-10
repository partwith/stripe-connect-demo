from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "stripe_connect_demo",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.vendor_tasks", "app.tasks.subscription_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "sync-all-vendors-every-5-minutes": {
            "task": "app.tasks.vendor_tasks.sync_all_vendors",
            "schedule": 300.0,
        },
        "renew-subscriptions-daily": {
            "task": "app.tasks.subscription_tasks.renew_due_subscriptions",
            "schedule": crontab(hour=0, minute=0),
        },
    },
)