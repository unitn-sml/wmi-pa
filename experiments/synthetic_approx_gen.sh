#!/bin/bash

SYN_DIR=synthetic_exp
DATA_DIR=$SYN_DIR/data_approx
RESULTS_DIR=$SYN_DIR/results_approx
MODELS=10
SEED=666

MIN_BOOL=0
MAX_BOOL=0
MIN_REAL=2
MAX_REAL=5
MIN_DEGREE=0
MAX_DEGREE=6
DEPTH=0

mkdir -p $DATA_DIR $RESULTS_DIR

for ((bool=$MIN_BOOL; bool<=$MAX_BOOL; bool++))
do
	for ((real=$MIN_REAL; real<=$MAX_REAL; real++))
	do
		for ((degree=$MIN_DEGREE; degree<=$MAX_DEGREE; degree+=2))
		do
			python3 randomModels.py -b $bool -r $real -d $DEPTH --poly-degree $degree -o $DATA_DIR -m $MODELS --seed $SEED
		done
	done
done
