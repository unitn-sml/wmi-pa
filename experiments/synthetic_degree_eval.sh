#!/bin/bash

SYN_DIR=synthetic_exp
DATA_DIR=$SYN_DIR/data_degree

for dir in $(ls -d $DATA_DIR/*)
do
	res_dir=$(sed "s+data+results+g" <<< $dir)
	mkdir -p $res_dir
	echo Evaluating $dir
	for mode in "SAPASK latte"
	do
		echo Mode $mode
		python3 evaluateModels.py $dir -o $res_dir -m $mode
	done

	for error in 0.005 0.01 0.05 0.1
	do
    echo "Mode SAPASK volesti, error $error, 10 seeds"
    python3 evaluateModels.py $dir -o $res_dir -m SAPASK volesti -e $error --seed 666 --n-seeds 10
  done

  error=0.01
  for N in 10000 100000 1000000
  do
    echo "Mode SAPASK volesti, N $N, 10 seeds"
    python3 evaluateModels.py $dir -o $res_dir -m SAPASK volesti -e $error -N $N --seed 666 --n-seeds 10
  done
done
