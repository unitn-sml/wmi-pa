#!/bin/bash

MLC_DIR=mlc

mkdir -p $MLC_DIR/plots

for qh in 0.0 0.25 0.5 0.75 1.0; do
  python3 plot.py $MLC_DIR/results/*$qh* -o $MLC_DIR/plots/ -f _dets-100-200-5-${qh}_cactus --cactus --timeout 1200 --title "H=${qh}"
done
