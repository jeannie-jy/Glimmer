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
COPY tests/ tests/
COPY .harness/ .harness/
COPY Makefile .
COPY README.md .
COPY --from=frontend /app/web/dist/ server/static/
EXPOSE 8000
ENV HARNESS_KEY_PASSWORD=""
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
