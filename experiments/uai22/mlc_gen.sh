#!/bin/bash

if [[ ! -d hybrid-benchmarks ]]; then
  echo "Cloning git@github.com:paolomorettin/hybrid-benchmarks.git..."
  git clone git@github.com:paolomorettin/hybrid-benchmarks.git
fi

cd hybrid-benchmarks/uai-22
for qh in 0.0 0.25 0.5 0.75 1.0
do
  python3 generate_dets.py 100 200 5 $qh 666
done

cd ../../
mkdir -p mlc/data
mv hybrid-benchmarks/uai-22/dets-* mlc/data

