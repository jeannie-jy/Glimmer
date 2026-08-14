FROM node:22-alpine AS frontend
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim AS backend
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY harness/ harness/
COPY server/ server/
COPY --from=frontend /app/server/static/ server/static/
# Agent workspace for deployments without a Docker sandbox socket
# (WORKSPACE_ROOT pins file operations here instead of the app source tree).
RUN mkdir -p /workspace
EXPOSE 8000
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
