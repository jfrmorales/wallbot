# syntax=docker/dockerfile:1

FROM python:3.11-slim

WORKDIR /app

# Instala dependencias del sistema para Playwright
RUN apt-get update && apt-get install -y \
    gcc \
    wget \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Instala dependencias de Python incluyendo Playwright
RUN pip install --no-cache-dir -r requirements.txt

# Instala navegadores de Playwright
RUN playwright install --with-deps

RUN mkdir -p /data /logs

COPY *.py ./

# Crea usuario no-root
RUN useradd --create-home --shell /bin/bash wallbot && \
    chown -R wallbot:wallbot /app /data /logs

USER wallbot

ENV DATABASE_PATH=/data/db.sqlite
ENV LOG_FILE=/logs/wallbot.log

EXPOSE 8080

CMD ["python", "main.py"]