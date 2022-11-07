#!/bin/bash

SYN_DIR=synthetic_exp

for dir in $(ls -d $SYN_DIR/data)
do
	mkdir -p $SYN_DIR/results/$dir
	echo Evaluating $dir
	for mode in XSDD XADD FXSDD "PA latte" "SAPA latte" "SAPASK latte"
	do
		echo Mode $mode
		python3 evaluateModels.py $SYN_DIR/data/$dir -o $SYN_DIR/results/$dir -m $mode 
	done
done
