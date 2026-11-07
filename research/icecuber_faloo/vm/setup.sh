#!/bin/bash
# VM side, idempotent. Clones the pinned commit of top-quarks/ARC-solution, builds it twice under /mnt/data/ice:
#   ARC-solution/  unmodified (eval = 0), for the README's own depth-2 check
#   build/         the same with the README's documented switch for test data (eval = 1 on line 75 of src/runner.cpp)
# Nothing from this directory goes back to the laptop except text output.
set -e
COMMIT=9407072659de1270358c2ba34c527785214dd68b
sudo mkdir -p /mnt/data && sudo chown "$USER:$USER" /mnt/data
mkdir -p /mnt/data/ice /dev/shm/ice && cd /mnt/data/ice
[ -d ARC-solution/.git ] || git clone -q https://github.com/top-quarks/ARC-solution.git
git -C ARC-solution checkout -q "$COMMIT"
if [ ! -x build/run ]; then
  rm -rf build && cp -r ARC-solution build && cd build
  sed -i '75s/int eval = 0;/int eval = 1;/' src/runner.cpp
  git diff --quiet HEAD -- Makefile headers safe_run.py
  [ "$(git diff --numstat | wc -l)" = "1" ] && [ "$(git diff --numstat | cut -f1,2 --output-delimiter=,)" = "1,1" ]
  make -j 40 run > make.log 2>&1
  cd ..
fi
cd /mnt/data/ice/build
echo "commit $(git rev-parse HEAD) binary $(sha256sum run | cut -c1-16) gcc $(g++ -dumpversion) nproc $(nproc) mem_gb $(free -g | awk 'NR==2{print $2}')"
git diff | grep '^[+-] ' || true
