# TAIVAS V7 Docker Deployment Guide

V7 packages TAIVAS as a portable Streamlit application that can run in Docker.

## Build

```bash
docker build -t taivas-v7 .
```

## Run

```bash
docker run -p 8501:8501 taivas-v7
```

Then open:

```text
http://localhost:8501
```

## Main entry point

```text
taivas_control_center_v7_docker_ready.py
```

## Streamlit Cloud

For Streamlit Cloud, keep using the same repository and set Main file path to:

```text
taivas_control_center_v7_docker_ready.py
```

Docker is not required for Streamlit Cloud, but the Dockerfile helps prepare TAIVAS for VPS, AWS, Azure, GCP, enterprise internal deployment, or technical review.

## Health check

The Dockerfile includes a basic Streamlit health check:

```text
/_stcore/health
```

This is useful when deploying to container platforms that need to know whether the app is alive.
