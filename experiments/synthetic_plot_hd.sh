#!/bin/bash

SYN_DIR=synthetic_exp

mkdir -p $SYN_DIR/plots

python3 plotUAI.py $SYN_DIR/results/models_r[579{11}]_b3_d3* -o $SYN_DIR/plots/ -f _syn_r5-11_b3_d3 --timeout 3600 --legend-pos 4
python3 plotUAI.py $SYN_DIR/results/models_r[579{11}]_b3_d3* -o $SYN_DIR/plots/ -f _syn_r5-11_b3_d3_cactus --cactus --timeout 3600 --legend-pos 4
# python3 plotUAI_cactus.py $SYN_DIR/results/* -o $SYN_DIR/plots/ -f _syn_r3_b3_d4-7_cactus
