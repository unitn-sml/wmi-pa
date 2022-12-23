#!/bin/bash

SYN_DIR=synthetic_exp

for dir in $(ls -d $SYN_DIR/data/models_r2_b0_d8*)
do
	res_dir=$(sed "s+data+results+g" <<< $dir)
	mkdir -p $res_dir
	echo Evaluating $dir
	for mode in "SAPASK latte" "SAPASK volesti" Rejection
	do
		echo Mode $mode
		python3 evaluateModels.py $dir -o $res_dir -m $mode 
	done
done
