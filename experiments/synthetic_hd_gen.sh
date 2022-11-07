#!/bin/bash

SYN_DIR=synthetic_exp
MODELS=5
SEED=666

MIN_BOOL=3
MAX_BOOL=3
MIN_REAL=5
MAX_REAL=11
MIN_DEPTH=3
MAX_DEPTH=3

mkdir -p $SYN_DIR/data $SYN_DIR/results

for ((bool=$MIN_BOOL; bool<=$MAX_BOOL; bool++))
do
	for ((real=$MIN_REAL; real<=$MAX_REAL; real+=2))
	do
		for ((depth=$MIN_DEPTH; depth<=$MAX_DEPTH; depth++))
		do
			python3 randomModels.py -b $bool -r $real -d $depth -o $SYN_DIR/data -m $MODELS --seed $SEED
		done
	done
done
