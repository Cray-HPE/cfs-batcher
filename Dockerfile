# Copyright 2019-2021 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# (MIT License)

# Base image
FROM arti.dev.cray.com/baseos-docker-master-local/alpine:3.12.4 as base
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

