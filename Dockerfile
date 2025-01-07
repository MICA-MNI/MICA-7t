# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set environment variable for dcm2niix v1.0.20240202
ENV PATH="/opt/dcm2niix-v1.0.20240202/bin:$PATH"

# Install dependencies and dcm2niix
RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
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
    /opt/conda/bin/conda init && \
    /opt/conda/bin/conda clean -afy

# Update PATH to include conda
ENV PATH="/opt/conda/bin:$PATH"

# Install jq v1.6
RUN apt-get update && apt-get install -y jq

# Install deno v2.0.6
RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="/root/.deno/bin:$PATH"

# Compile bids-validator v2.0.0
RUN deno compile -ERN -o bids-validator jsr:@bids/validator

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

ENV PATH="/app/functions:$PATH"

# Run the application
ENTRYPOINT ["7t2bids"]
