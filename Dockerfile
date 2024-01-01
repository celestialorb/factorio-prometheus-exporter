FROM docker.io/library/python:3-slim

RUN useradd --create-home --shell /bin/bash exporter
USER exporter

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --user --requirement /tmp/requirements.txt

COPY exporter.py /exporter.py
ENTRYPOINT ["/exporter.py", "run"]
