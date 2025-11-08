FROM python:3.11-slim AS base

# Create a dedicated virtual environment for smaller final image
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

FROM base AS builder
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

FROM base AS runtime
WORKDIR /app

# Install git for commit extraction
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Copy only the already-built virtualenv from builder layer
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Copy application source
COPY . /app

# Ensure local package imports resolve without needing PYTHONPATH in runtime commands
ENV PYTHONPATH=/app

# Default to running the API server; CLI still available via docker run ... python src/generate_notes.py
EXPOSE 5000
CMD ["python", "src/server.py"]
