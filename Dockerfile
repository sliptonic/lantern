# Lantern — single-container image.
# Bundles the FastAPI app + headless Chromium (via Playwright) + git.
#
# Pinned to bookworm (Debian 12): Playwright 1.49's `--with-deps` knows
# bookworm's package names. The plain `python:3.12-slim` tag now points at
# Debian 13 (trixie), where Playwright tries to install renamed/removed font
# packages (ttf-unifont, ttf-ubuntu-font-family) and the install fails.
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_DIR=/data

# git is needed for the content store (versioning).
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching).
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Chromium + its OS dependencies for Playwright.
RUN playwright install --with-deps chromium

COPY app ./app

# Runtime data (content git repo, sqlite db, logo) lives on a mounted volume.
VOLUME ["/data"]
EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
