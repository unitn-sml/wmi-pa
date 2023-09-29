#!/bin/bash

SYN_DIR=synthetic_exp
DATA_DIR=$SYN_DIR/data_approx
RESULTS_DIR=$SYN_DIR/results_approx
MODELS=10
SEED=666

MIN_REAL=2
MAX_REAL=8
MIN_DEGREE=0
MAX_DEGREE=6
BOOL=0
DEPTH=5

mkdir -p $DATA_DIR $RESULTS_DIR

FIX_DEGREE=4
FIX_REALS=3
for ((real=$MIN_REAL; real<=$MAX_REAL; real++))
do
  python3 randomModels.py -b $BOOL -r $real -d $DEPTH --no-times --poly-degree $FIX_DEGREE -o $DATA_DIR -m $MODELS --seed $SEED
done
for ((degree=$MIN_DEGREE; degree<=$MAX_DEGREE; degree+=2))
do
  python3 randomModels.py -b $BOOL -r $FIX_REALS -d $DEPTH --no-times --poly-degree $degree -o $DATA_DIR -m $MODELS --seed $SEED
done

