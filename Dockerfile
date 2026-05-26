# ============================================================
# Stage 1: Build dcm2niix from source
# ============================================================
FROM python:3.12-slim AS dcm2niix-builder

RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
        cmake \
        curl \
        g++ \
        gcc \
        git \
        make \
        zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/rordenlab/dcm2niix /tmp/dcm2niix \
    && cd /tmp/dcm2niix \
    && git fetch --tags \
    && git checkout v1.0.20260416 \
    && mkdir /tmp/dcm2niix/build \
    && cd /tmp/dcm2niix/build \
    && cmake -DCMAKE_INSTALL_PREFIX:PATH=/opt/dcm2niix-v1.0.20260416 .. \
    && make \
    && make install \
    && rm -rf /tmp/dcm2niix

# ============================================================
# Stage 2: Final image
# ============================================================
FROM python:3.12-slim

# ---------- dcm2niix ----------
COPY --from=dcm2niix-builder /opt/dcm2niix-v1.0.20260416 /opt/dcm2niix-v1.0.20260416
ENV PATH="/opt/dcm2niix-v1.0.20260416/bin:$PATH"

# ---------- Runtime system deps (curl, pigz, bc, wget, unzip, jq) ----------
RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
        bc \
        curl \
        jq \
        pigz \
        unzip \
        wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ---------- Python deps (no Conda needed — pydicom is pure Python) ----------
RUN pip install --no-cache-dir pydicom nibabel

# --------------------------------
# Install deno v2.2.3
ENV DENO_DIR=/opt/deno_cache
ENV DENO_INSTALL="/opt/.deno"
RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="$DENO_INSTALL/bin:$PATH"

# --------------------------------
# Compile bids-validator v2.0.3
RUN deno compile -ERN -o bids-validator jsr:@bids/validator

# ---------- Non-root user ----------
RUN useradd -m -u 1000 appuser

# ---------- Application ----------
WORKDIR /app
COPY . /app
RUN chmod +x /app/functions/dcm2bids.py
ENV PATH="/app/functions:$PATH"

RUN chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["/app/functions/dcm2bids.py"]