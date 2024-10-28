FROM docker.io/library/python:3-slim
LABEL org.opencontainers.image.description A Prometheus exporter for a Factorio server.

RUN useradd --create-home --shell /bin/bash exporter
RUN mkdir --parents /opt/exporter
WORKDIR /opt/exporter
USER exporter

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --user --requirement /tmp/requirements.txt

COPY collection collection
COPY exporter.py exporter.py
ENTRYPOINT ["/opt/exporter/exporter.py", "run"]
