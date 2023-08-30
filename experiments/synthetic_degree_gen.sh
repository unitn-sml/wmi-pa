#!/bin/bash

SYN_DIR=synthetic_exp
DATA_DIR=$SYN_DIR/data_degree
RESULTS_DIR=$SYN_DIR/results_degree
MODELS=10
SEED=666

MIN_BOOL=0
MAX_BOOL=0
MIN_REAL=3
MAX_REAL=3
MIN_DEGREE=0
MAX_DEGREE=3
DEPTH=0

mkdir -p $DATA_DIR $RESULTS_DIR

for ((bool=$MIN_BOOL; bool<=$MAX_BOOL; bool++))
do
	for ((real=$MIN_REAL; real<=$MAX_REAL; real++))
	do
		for ((degree=$MIN_DEGREE; degree<=$MAX_DEGREE; degree++))
		do
			python3 randomModels.py -b $bool -r $real -d $DEPTH --poly-degree $degree -o $DATA_DIR -m $MODELS --seed $SEED
		done
	done
done
