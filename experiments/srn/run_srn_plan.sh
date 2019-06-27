#!/bin/bash

if [ $# -eq 0 ]
then
    echo "No output argument"
    exit
fi

if [ ! -e data/MAR15.csv ]
then
    cd data
    gunzip MAR15.csv.tar.gz
    tar -xf MAR15.csv.tar
    cd ..
fi

if [ ! -e $1 ]
then
    mkdir $1
else
    echo "Folder '$1' already exists"
    exit
fi

for i in {1..2}
do
    python3 srnplan.py generate -i data/MAR15.csv -s 42 --iterations=10 --min-length=$i --max-length=$i -o $1/AIJ_PLAN_s42_i10_$i.experiment
done

for i in {1..2}
do
    for cache in {-1..3}
    do
        python3 srnplan.py simulate -i $1/AIJ_PLAN_s42_i10_$i.experiment -m WMI-PA -e xor -c $cache -o $1/AIJ_PLAN_s42_i10_$i\_cache_$cache.results_wmipa
    done
done

# plot
python3 srnplan.py plot -i $1/AIJ_PLAN_s42_i10_{1..2}_cache_{-1..3}.results_wmipa -o $1/AIJ_PLAN_plot

rm -r tmp*
