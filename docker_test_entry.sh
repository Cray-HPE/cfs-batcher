#!/bin/sh
# Copyright 2020, Cray Inc. All Rights Reserved.
set -e
set -o pipefail

mkdir -p /results
python3 -m pip freeze 2>&1 | tee /results/pip_freeze.out
export PYTHONPATH="/app/lib/"
nosetests -v \
 -w /app/lib/test \
 --with-xunit \
 --xunit-file=/results/nosetests.xml \
 --with-coverage \
 --cover-erase \
 --cover-package=batcher \
 --cover-branches \
 --cover-inclusive \
 --cover-html \
 --cover-html-dir=/results/coverage \
 --cover-xml \
 --cover-xml-file=/results/coverage.xml \
 2>&1 | tee /results/nosetests.out
