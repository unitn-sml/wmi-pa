#!/bin/bash

SYN_DIR=synthetic_exp
DATA_DIR=$SYN_DIR/data

for dir in $(ls -d $DATA_DIR/*)
do
	res_dir=$(sed "s+data+results+g" <<< $dir)
	mkdir -p $res_dir
	echo Evaluating $dir
	for mode in XSDD XADD FXSDD "PA latte" "SAPA latte" "SAPASK latte" "SAPASK symbolic"
	do
		echo Mode $mode
		python3 evaluateModels.py $dir -o $res_dir -m $mode 
	done

  error=0.1
	for N in 100 1000 10000
	do
    echo "Mode SAPASK volesti, N $N, 5 seeds"
    python3 evaluateModels.py "$dir" -o "$res_dir" -m SAPASK volesti -e $error -N $N --seed 666 --n-seeds 5
  done
done
