#!/bin/bash

MLC_DIR=mlc

for dir in $(ls $MLC_DIR/data)
do
        mkdir -p $MLC_DIR/results/$dir
	echo Evaluating $dir
	for mode in SAPA PA XSDD XADD FXSDD
        do
                echo Mode $mode
                python3 evaluateModels.py $MLC_DIR/data/$dir -o $MLC_DIR/results/$dir -m $mode --timeout 1200
        done
done
