import os
import socket

UNFAZED_SETTINGS = {
    "LIFESPAN": ["unfazed_taskiq.lifespan.TaskiqLifeSpan"],
    "ROOT_URLCONF": "entry.routes",
    "INSTALLED_APPS": ["app"],
}


UNFAZED_PROMETHEUS_SETTINGS = {
    "HOSTNAME": socket.gethostname(),
    "PROJECT": "unfazed_prometheus",
    "CLIENT_CLASS": "unfazed_prometheus.settings.PrometheusSettings",
    "PROMETHEUS_MULTIPROC_DIR": os.getenv("PROMETHEUS_MULTIPROC_DIR", "/prometheus"),
}
