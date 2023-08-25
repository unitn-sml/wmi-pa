#!/bin/bash

SYN_DIR=synthetic_exp

for dir in $(ls -d $SYN_DIR/data/*)
do
	res_dir=$(sed "s+data+results+g" <<< $dir)
	mkdir -p $res_dir
	echo Evaluating $dir
	for mode in XSDD XADD FXSDD "PA latte" "SAPA latte" "SAPASK latte" "SAPASK symbolic"
	do
		echo Mode $mode
		python3 evaluateModels.py $dir -o $res_dir -m $mode 
	done
	echo "Mode SAPASK volesti, error 0.005, 10 seeds"
	python3 evaluateModels.py $dir -o $res_dir -m SAPASK volesti -e 0.005 --seed 666 --n-seeds 10
	echo "Mode SAPASK volesti, error 0.01, 10 seeds"
	python3 evaluateModels.py $dir -o $res_dir -m SAPASK volesti -e 0.01  --seed 666 --n-seeds 10
	echo "Mode SAPASK volesti, error 0.05, 10 seeds"
	python3 evaluateModels.py $dir -o $res_dir -m SAPASK volesti -e 0.05  --seed 666 --n-seeds 10
	echo "Mode SAPASK volesti, error 0.1, 10 seeds"
	python3 evaluateModels.py $dir -o $res_dir -m SAPASK volesti -e 0.1   --seed 666 --n-seeds 10
done
