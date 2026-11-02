FROM python:3.13-slim@sha256:2d44738ebf4ce5f63b9d9ea871e9c7cfdc0426f7b0c97cac915fd88ded1d86bb AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore
WORKDIR /srv/backend
COPY requirements.in requirements-test.in requirements.lock ./
RUN pip install --no-cache-dir -r requirements.in -c requirements.lock

FROM base AS runtime
COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
RUN useradd --create-home --uid 1000 hotel
USER hotel
CMD ["uvicorn", "--factory", "app.main:create_app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS test
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN pip install --no-cache-dir -r requirements-test.in -c requirements.lock \
    && playwright install --with-deps chromium
