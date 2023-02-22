#!/bin/bash

SYN_DIR=synthetic_exp

mkdir -p $SYN_DIR/plots

python3 plot.py $SYN_DIR/results/models_r2_b0_d8* -o $SYN_DIR/plots/ -f _syn_r2_b0_d8 --timeout 3600 --legend-pos 4
python3 plot.py $SYN_DIR/results/models_r2_b0_d8* -o $SYN_DIR/plots/ -f _syn_r2_b0_d8_cactus --cactus --timeout 3600 --legend-pos 4
# python3 plotUAI_cactus.py $SYN_DIR/results/* -o $SYN_DIR/plots/ -f _syn_r3_b3_d4-7_cactus