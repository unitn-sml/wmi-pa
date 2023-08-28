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

	for error in 0.005 0.01 0.05 0.1
	do
    echo "Mode SAPASK volesti, error $error, 10 seeds"
    python3 evaluateModels.py $dir -o $res_dir -m SAPASK volesti -e $error --seed 666 --n-seeds 10
  done
done
