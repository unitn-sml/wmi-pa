#!/bin/bash

SYN_DIR=synthetic_exp

for dir in $(ls -d $SYN_DIR/data/models_r[579{11}]_b3_d3*)
do
	mkdir -p $SYN_DIR/results/$dir
	echo Evaluating $dir
	for mode in "SAPASK latte" "SAPASK volesti" Rejection
	do
		echo Mode $mode
		python3 evaluateModels.py $SYN_DIR/data/$dir -o $SYN_DIR/results/$dir -m $mode 
	done
done
