#!/bin/bash

MLC_DIR=mlc

for dir in $(ls -d $MLC_DIR/data)
do
	res_dir=$(sed "s+data+results+g" <<< $dir)
  mkdir -p $res_dir
	echo Evaluating $dir
	for mode in XSDD XADD FXSDD "PA latte" "SAPA latte" "SAPASK latte"
        do
                echo Mode $mode
                python3 evaluateModels.py $dir -o $res_dir --timeout 1200 -m $mode
        done
done
