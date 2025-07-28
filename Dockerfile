# Use Python 3.11 slim base image
FROM python:3.11-slim

# Re-declare ARG variables to make them available after FROM
ARG APP_HOME=/app
ARG GITHUB_REPO=https://github.com/unclecode/crawl4ai.git
ARG GITHUB_BRANCH=main
ARG USE_LOCAL=false
ARG ENABLE_GPU=false
ARG TARGETARCH=amd64
ARG INSTALL_TYPE=basic

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies for Chrome and crawl4ai
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    gnupg \
    xvfb \
    unzip \
    git \
    cmake \
    pkg-config \
    python3-dev \
    libjpeg-dev \
    redis-server \
    supervisor \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome/Chromium based on architecture
RUN if [ "$TARGETARCH" = "amd64" ]; then \
        wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
        && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
        && apt-get update \
        && apt-get install -y google-chrome-stable \
        && rm -rf /var/lib/apt/lists/*; \
    else \
        apt-get update \
        && apt-get install -y --no-install-recommends chromium \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*; \
    fi

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get dist-upgrade -y \
    && rm -rf /var/lib/apt/lists/*

RUN if [ "$ENABLE_GPU" = "true" ] && [ "$TARGETARCH" = "amd64" ] ; then \
    apt-get update && apt-get install -y --no-install-recommends \
    nvidia-cuda-toolkit \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* ; \
else \
    echo "Skipping NVIDIA CUDA Toolkit installation (unsupported platform or GPU disabled)"; \
fi

RUN if [ "$TARGETARCH" = "arm64" ]; then \
    echo "🦾 Installing ARM-specific optimizations"; \
    apt-get update && apt-get install -y --no-install-recommends \
    libopenblas-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*; \
elif [ "$TARGETARCH" = "amd64" ]; then \
    echo "🖥️ Installing AMD64-specific optimizations"; \
    apt-get update && apt-get install -y --no-install-recommends \
    libomp-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*; \
else \
    echo "Skipping platform-specific optimizations (unsupported platform)"; \
fi

# Create a non-root user and group
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

# Create and set permissions for appuser home directory
RUN mkdir -p /home/appuser && chown -R appuser:appuser /home/appuser

# Create installation script
RUN echo '#!/bin/bash\n\
if [ "$USE_LOCAL" = "true" ]; then\n\
    echo "📦 Installing from local source..."\n\
    pip install --no-cache-dir /tmp/project/\n\
else\n\
    echo "🌐 Installing from GitHub..."\n\
    for i in {1..3}; do \n\
        git clone --branch ${GITHUB_BRANCH} ${GITHUB_REPO} /tmp/crawl4ai && break || \n\
        { echo "Attempt $i/3 failed! Taking a short break... ☕"; sleep 5; }; \n\
    done\n\
    pip install --no-cache-dir /tmp/crawl4ai\n\
fi' > /tmp/install.sh && chmod +x /tmp/install.sh

# Set up Chrome for headless mode
RUN if [ "$TARGETARCH" = "amd64" ]; then \
        echo "export CHROME_BIN=/usr/bin/google-chrome" >> /etc/environment \
        && echo "export CHROME_PATH=/usr/bin/google-chrome" >> /etc/environment; \
    else \
        echo "export CHROME_BIN=/usr/bin/chromium" >> /etc/environment \
        && echo "export CHROME_PATH=/usr/bin/chromium" >> /etc/environment; \
    fi

ENV CHROME_BIN=${CHROME_BIN:-/usr/bin/chromium} \
    CHROME_PATH=${CHROME_PATH:-/usr/bin/chromium}

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Set ownership for appuser
RUN chown -R appuser:appuser /app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (needed for crawl4ai)
RUN playwright install chromium \
    && playwright install-deps chromium

# Copy application code
COPY . .

# Set ownership and permissions for appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Install additional packages if needed
RUN if [ "$INSTALL_TYPE" = "all" ] ; then \
        pip install --no-cache-dir \
            torch \
            torchvision \
            torchaudio \
            scikit-learn \
            nltk \
            transformers \
            tokenizers && \
        python -m nltk.downloader punkt stopwords ; \
    fi

# Install crawl4ai and verify installation
RUN pip install --no-cache-dir --upgrade pip && \
    /tmp/install.sh && \
    python -c "import crawl4ai; print('✅ crawl4ai is ready to rock!')" && \
    python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright is feeling dramatic!')"

# Switch back to root to install browsers for the user
USER root

# Install Playwright browsers for the appuser
RUN su - appuser -c "playwright install chromium"

# Ensure proper ownership
RUN chown -R appuser:appuser /home/appuser/.cache

# Switch back to appuser
USER appuser

# Expose the port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"] 