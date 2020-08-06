# Copyright 2020, Cray Inc., A Hewlett Packard Enterprises Company, All rights reserved.

# Base image
FROM dtr.dev.cray.com/baseos/alpine:3.11.5 as base
WORKDIR /app
COPY constraints.txt requirements.txt ./
RUN apk add --no-cache gcc g++ python3-dev musl-dev libffi-dev openssl-dev && \
    PIP_INDEX_URL=http://dst.us.cray.com/dstpiprepo/simple \
    PIP_TRUSTED_HOST=dst.us.cray.com \
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

