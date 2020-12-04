# Copyright 2019-2020 Hewlett Packard Enterprise Development LP

# Base image
FROM dtr.dev.cray.com/baseos/alpine:3.12.0 as base
WORKDIR /app
COPY constraints.txt requirements.txt ./
RUN apk add --no-cache gcc g++ python3-dev py3-pip musl-dev libffi-dev openssl-dev && \
    PIP_INDEX_URL=https://arti.dev.cray.com:443/artifactory/api/pypi/pypi-remote/simple \
    pip3 install --no-cache-dir -U pip && \
    pip3 install --no-cache-dir -r requirements.txt
COPY src/batcher/ lib/batcher/

# Testing Image
FROM base as testing
WORKDIR /app/
COPY src/test lib/test/
COPY docker_test_entry.sh .
COPY test-requirements.txt .
RUN pip3 install --no-cache-dir -r test-requirements.txt
CMD [ "./docker_test_entry.sh" ]

# Codestyle reporting
FROM testing as codestyle
WORKDIR /app/
COPY docker_codestyle_entry.sh setup.cfg ./
CMD [ "./docker_codestyle_entry.sh" ]

# Application Image
FROM base as application
ENV PYTHONPATH "/app/lib/"
ENTRYPOINT [ "python3", "-m", "batcher" ]

