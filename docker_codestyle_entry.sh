#!/bin/sh
# Copyright 2020, Cray Inc. All Rights Reserved.

set -e
set -o pipefail
cd /app/
flake8 --config /app/setup.cfg /app/lib/batcher 2>&1 | tee /results/flake8.out
