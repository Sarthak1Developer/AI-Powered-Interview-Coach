FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PORT=7860

# Install system dependencies with retry
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libespeak1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Upgrade pip first
RUN pip install --upgrade pip setuptools wheel

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

# Hugging Face Spaces commonly runs containers with UID 1000.
# Ensure runtime-generated files are writable in /app.
RUN mkdir -p /app/reports \
    && chown -R 1000:1000 /app

USER 1000

EXPOSE 7860
ENTRYPOINT ["python", "-m", "server.app"]
