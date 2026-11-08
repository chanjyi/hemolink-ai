# HemoLink AI — container image (Railway, Fly.io, Hugging Face Spaces, Google Cloud Run, any VM with Docker)
FROM python:3.11-slim

# OpenCV (used by the photo reader) needs these system libraries
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# run as a normal user (required by Hugging Face Spaces, good practice everywhere)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH PYTHONUNBUFFERED=1 \
    HEMOLINK_ENV=production PORT=7860
WORKDIR /home/user/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
COPY --chown=user . .

EXPOSE 7860
# Set HEMOLINK_SECRET_KEY as a secret on your host. Set HEMOLINK_OCR=off on machines with < 1 GB RAM.
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips "*"
