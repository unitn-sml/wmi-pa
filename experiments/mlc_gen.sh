#!/bin/bash


N_MIN=100
N_MAX=200
N_QUERIES=5
SEED=666

if [[ ! -d hybrid-benchmarks ]]; then
  echo "Cloning https://github.com/paolomorettin/hybrid-benchmarks.git..."
  git clone https://github.com/paolomorettin/hybrid-benchmarks.git
fi

cd hybrid-benchmarks/uai-22
for qh in 0.0 0.25 0.5 0.75 1.0; do
  python3 generate_dets.py $N_MIN $N_MAX $N_QUERIES $qh $SEED
done

cd ../../
mkdir -p mlc/data
mv hybrid-benchmarks/uai-22/dets-* mlc/data
