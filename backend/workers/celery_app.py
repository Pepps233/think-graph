import ssl

from celery import Celery
from app.config import settings

celery_app = Celery(
    "thinkgraph",
    broker=settings.celery_broker_url_with_ssl,
    backend=settings.celery_broker_url_with_ssl,
    include=["workers.tasks"],
)

_conf = dict(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    broker_transport_options={
        "socket_connect_timeout": 5,
        "socket_timeout": 5,
    },
)

if settings.celery_broker_url.startswith("rediss://"):
    _conf["broker_use_ssl"] = {"ssl_cert_reqs": ssl.CERT_NONE}
    _conf["redis_backend_use_ssl"] = {"ssl_cert_reqs": ssl.CERT_NONE}

celery_app.conf.update(**_conf)
