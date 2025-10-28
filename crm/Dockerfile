FROM python:3.12.4

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /webapp

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    bash \
    cmake \
    pkg-config \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Copy ONLY requirements first (better caching)
COPY requirements.txt /webapp/requirements.txt

# Install Python dependencies (this layer will be cached if requirements.txt doesn't change)
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script
COPY entrypoint.sh /webapp/entrypoint.sh
RUN chmod +x /webapp/entrypoint.sh

# Copy application code (this changes most often, so it's last)
COPY . /webapp/

EXPOSE 8000

ENTRYPOINT ["/webapp/entrypoint.sh"]
