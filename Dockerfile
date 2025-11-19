# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set environment variable for dcm2niix v1.0.20240202
ENV PATH="/opt/dcm2niix-v1.0.20240202/bin:$PATH"

# Install dependencies and dcm2niix
RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           bc \
           cmake \
           curl \
           g++ \
           gcc \
           git \
           make \
           pigz \
           unzip \
           wget \
           zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && git clone https://github.com/rordenlab/dcm2niix /tmp/dcm2niix \
    && cd /tmp/dcm2niix \
    && git fetch --tags \
    && git checkout v1.0.20240202 \
    && mkdir /tmp/dcm2niix/build \
    && cd /tmp/dcm2niix/build \
    && cmake  -DCMAKE_INSTALL_PREFIX:PATH=/opt/dcm2niix-v1.0.20240202 .. \
    && make \
    && make install \
    && rm -rf /tmp/dcm2niix

# Download and install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /miniconda.sh && \
    bash /miniconda.sh -b -p /opt/conda && \
    rm /miniconda.sh && \
    /opt/conda/bin/conda clean -afy

# Configure conda: remove default channels, use conda-forge only
RUN /opt/conda/bin/conda config --system --remove-key channels && \
    /opt/conda/bin/conda config --system --add channels conda-forge && \
    /opt/conda/bin/conda config --system --set channel_priority strict

# Set PATH so we can run conda directly
ENV PATH /opt/conda/bin:$PATH

# Install pydicom
RUN conda install -y pydicom && \
    conda clean -afy

# Install jq v1.6
RUN apt-get update && apt-get install -y curl && \
    curl -L -o /usr/bin/jq https://github.com/stedolan/jq/releases/download/jq-1.6/jq-linux64 && \
    chmod +x /usr/bin/jq && \
    jq --version

# Install deno v2.2.3
ENV DENO_DIR=/opt/deno_cache
ENV DENO_INSTALL="/opt/.deno"
RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="$DENO_INSTALL/bin:$PATH"

# Compile bids-validator v2.0.3
RUN deno compile -ERN -o bids-validator jsr:@bids/validator

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

ENV PATH="/app/functions:$PATH"

# Run the application
ENTRYPOINT ["/app/functions/dcm2bids.py"]
