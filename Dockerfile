# Multi-stage build for optimized image size
FROM python:3.14-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.14-slim

# Build arguments for versioning and metadata
ARG BUILD_VERSION=dev
ARG BUILD_SHA=unknown
ARG BUILD_TIME=unknown
ARG BUILD_NUMBER=0
ARG BUILD_BRANCH=unknown

# Set environment variables for build metadata
ENV BUILD_VERSION=${BUILD_VERSION} \
    BUILD_SHA=${BUILD_SHA} \
    BUILD_TIME=${BUILD_TIME} \
    BUILD_NUMBER=${BUILD_NUMBER} \
    BUILD_BRANCH=${BUILD_BRANCH}

# Labels for image metadata (OCI standard)
LABEL org.opencontainers.image.version="${BUILD_VERSION}" \
      org.opencontainers.image.revision="${BUILD_SHA}" \
      org.opencontainers.image.created="${BUILD_TIME}" \
      org.opencontainers.image.title="Amani Escrow Backend" \
      org.opencontainers.image.description="Secure escrow backend for Amani platform" \
      org.opencontainers.image.source="https://github.com/praiseunite/amani-backend" \
      org.opencontainers.image.vendor="Amani"

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Create logs directory
RUN mkdir -p logs

# Create a build-info file for runtime access
RUN echo "{\n\
  \"version\": \"${BUILD_VERSION}\",\n\
  \"commit_sha\": \"${BUILD_SHA}\",\n\
  \"build_time\": \"${BUILD_TIME}\",\n\
  \"build_number\": \"${BUILD_NUMBER}\",\n\
  \"build_branch\": \"${BUILD_BRANCH}\"\n\
}" > /app/build-info.json

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health', timeout=5)" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
