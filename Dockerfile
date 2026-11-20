FROM node:22-bookworm-slim AS web
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./
RUN npm ci
COPY frontend/ ./
ENV VITE_HOSTED_DEMO=true
RUN npm run build

FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HUB_DISABLE_TELEMETRY=1
WORKDIR /opt/yesrole/backend
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./
RUN python -m pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu \
    && python -m pip install -r requirements.txt
COPY backend/app ./app
COPY --from=web /build/dist ../frontend/dist
RUN python -m app.download_model
ENV YESROLE_OFFLINE=true YESROLE_DB=/tmp/yesrole.sqlite3 HF_HOME=/tmp/huggingface OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
USER 10001:10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.hosted:create_default_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]

