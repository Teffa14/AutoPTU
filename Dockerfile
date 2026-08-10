FROM node:24-alpine AS web-build
WORKDIR /build/career_web
COPY career_web/package.json career_web/package-lock.json ./
RUN npm ci
COPY career_web/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY auto_ptu ./auto_ptu
COPY scripts ./scripts
COPY tests ./tests
COPY files ./files
COPY PTUDatabase-main ./PTUDatabase-main
COPY "IMPLEMENTATION FILES" "./IMPLEMENTATION FILES"
COPY --from=web-build /build/auto_ptu/api/static/career ./auto_ptu/api/static/career
RUN pip install --no-cache-dir .
EXPOSE 10000
CMD ["sh", "-c", "uvicorn auto_ptu.api.server:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
