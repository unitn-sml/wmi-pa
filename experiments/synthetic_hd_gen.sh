#!/bin/bash

SYN_DIR=synthetic_exp
MODELS=10
SEED=666

MIN_BOOL=0
MAX_BOOL=0
MIN_REAL=2
MAX_REAL=2
MIN_DEPTH=8
MAX_DEPTH=8

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
