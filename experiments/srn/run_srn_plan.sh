#!/bin/bash

# folders
out_folder=output_plan
prob_folder=problems
res_folder=results
figure_folder=figures


# extract data if needed
if [ ! -e data/MAR15.csv ]
then
    cd data
    gunzip MAR15.csv.tar.gz
    tar -xf MAR15.csv.tar
    cd ..
fi


# create output folders
mkdir $out_folder $out_folder/$prob_folder $out_folder/$res_folder $out_folder/$figure_folder 2> /dev/null


# generate problems
for size in {1..8}
do
    if [ ! -e $out_folder/$prob_folder/AIJ_PLAN_s42_i10_$size.experiment ]
    then
        if ! python3 srnplan.py generate -i data/MAR15.csv -s 42 --iterations=10 --min-length=$size --max-length=$size -o $out_folder/$prob_folder/AIJ_PLAN_s42_i10_$size.experiment
        then
            echo "Generation error on following command:"
            echo python3 srnplan.py generate -i data/MAR15.csv -s 42 --iterations=10 --min-length=$size --max-length=$size -o $out_folder/$prob_folder/AIJ_PLAN_s42_i10_$size.experiment
            echo "Terminated."
            exit 1
        fi
    else
        echo "$out_folder/$prob_folder/AIJ_PLAN_s42_i10_$size.experiment already exist. Skipped.."
    fi
done


# execute problems
for size in {1..8}
do
    for cache in {-1..3}
    do
        if [ ! -e $out_folder/$res_folder/AIJ_PLAN_s42_i10_$size\_cache_$cache.results_wmipa ]
        then
            if ! python3 srnplan.py simulate -i $out_folder/$prob_folder/AIJ_PLAN_s42_i10_$size.experiment -m WMI-PA -e xor -c $cache -o $out_folder/$res_folder/AIJ_PLAN_s42_i10_$size\_cache_$cache.results_wmipa
            then
                echo "Simulation error on following command:"
                echo python3 srnplan.py simulate -i $out_folder/$prob_folder/AIJ_PLAN_s42_i10_$size.experiment -m WMI-PA -e xor -c $cache -o $out_folder/$res_folder/AIJ_PLAN_s42_i10_$size\_cache_$cache.results_wmipa
                echo "Terminated."
                exit 1
            fi
        else
            echo "Results of problem with size $size with cache $cache already exists: skipped..."
        fi
    done
done


# plot
python3 srnplan.py plot -i $out_folder/$res_folder/AIJ_PLAN_s42_i10_{1..8}_cache_{-1..3}.results_wmipa -o $out_folder/$figure_folder/AIJ_PLAN_plot
