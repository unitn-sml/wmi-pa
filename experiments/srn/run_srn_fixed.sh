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

python3 srn.py generate -i data/MAR15.csv -s 42 --iterations=10 --min-length=1 --max-length=8 -o $1/AIJ_SRN_s42_i10_1_8.experiment &&

for mode in WMI-BC WMI-ALLSMT WMI-PA
do
    for i in {-1..3}
    do
        python3 srn.py simulate -i $1/AIJ_SRN_s42_i10_1_8.experiment -m $mode -e xor -c $i -o $1/AIJ_SRN_s42_i10_1_8_cache_$i.results_$mode
    done
done

# plot
for mode in WMI-BC WMI-ALLSMT WMI-PA
do
    python3 srn.py plot -i $1/AIJ_SRN_s42_i10_1_8_cache_{-1,0,1,2,3}.results_$mode -o $1/AIJ_SRN_plot
done

rm -r tmp*
