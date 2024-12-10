FROM python:3.11-slim-buster

WORKDIR /opt/dagster/app

RUN apt-get update && \
apt-get install -y --no-install-recommends \
gcc && \
apt-get clean && \
rm -rf /var/lib/apt/lists/*

# Project initialization
RUN pip install uv
COPY requirements.txt /opt/dagster/app/requirements.txt
RUN uv pip install --no-cache-dir -r /opt/dagster/app/requirements.txt

# Copy code and workspace to /opt/dagster/app
COPY src /opt/dagster/app/src
COPY pyproject.toml /opt/dagster/app/pyproject.toml
COPY README.md /opt/dagster/app/README.md
RUN pip install --no-cache-dir -e .