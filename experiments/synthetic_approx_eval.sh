#!/bin/bash

SYN_DIR=synthetic_exp
DATA_DIR=$SYN_DIR/data_approx
SEED=666
N_VOLESTI_INSTANCES=10
ERROR=0.01

for dir in $(ls -d $DATA_DIR/*); do
  res_dir=$(sed "s+data+results+g" <<<$dir)
  mkdir -p $res_dir
  echo Evaluating $dir

  echo Mode "SAPASK latte";
  python3 evaluateModels.py $dir -o $res_dir -m SAPASK latte

  for N in 10000 100000 1000000; do
    echo "Mode SAPASK volesti, error $ERROR, N $N, 10 seeds"
    python3 evaluateModels.py $dir -o $res_dir -m SAPASK volesti -e ERROR -N $N --seed $SEED --n-seeds $N_VOLESTI_INSTANCES
  done

done
