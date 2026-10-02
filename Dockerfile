FROM node:20-alpine AS frontend
# frontend depends on the local client package via "file:../clients/typescript",
# so both directories keep their repository-relative layout under /src.
WORKDIR /src/frontend
COPY clients/typescript/ /src/clients/typescript/
COPY frontend/package.json frontend/package-lock.json* ./
RUN if [ -s package-lock.json ] && grep -q '"packages"' package-lock.json; then npm ci; else npm install; fi
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	MINIAPP_STATIC_DIR=/app/frontend/dist
WORKDIR /app
COPY pyproject.toml ./
COPY app/ ./app/
RUN pip install --no-cache-dir .
COPY . .
COPY --from=frontend /src/frontend/dist ./frontend/dist
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
