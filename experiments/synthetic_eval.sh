#!/bin/bash

SYN_DIR=synthetic_exp

for dir in $(ls -d $SYN_DIR/data)
do
	res_dir=$(sed "s+data+results+g" <<< $dir)
	mkdir -p $res_dir
	echo Evaluating $dir
	for mode in XSDD XADD FXSDD "PA latte" "SAPA latte" "SAPASK latte"
	do
		echo Mode $mode
		python3 evaluateModels.py $dir -o $res_dir -m $mode 
	done
done
