#!/bin/bash

# folders
out_folder=output_fixed
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
if [ ! -e $out_folder/$prob_folder/AIJ_SRN_s42_i10_1_8.experiment ]
then
    if ! python3 srn.py generate -i data/MAR15.csv -s 42 --iterations=10 --min-length=1 --max-length=8 -o $out_folder/$prob_folder/AIJ_SRN_s42_i10_1_8.experiment
    then
        echo "Generation error on following command:"
        echo python3 srn.py generate -i data/MAR15.csv -s 42 --iterations=10 --min-length=1 --max-length=8 -o $out_folder/$prob_folder/AIJ_SRN_s42_i10_1_8.experiment
        echo "Terminated."
        exit 1
    fi
else
    echo "$out_folder/$prob_folder/AIJ_SRN_s42_i10_1_8.experiment already exists"
    echo "Skipping generation step (delete file if you want to repeat it again)"
fi


# execute problems
for mode in WMI-PA WMI-PA-NL
do
    for cache in {-1..0}
    do
        if [ ! -e $out_folder/$res_folder/AIJ_SRN_s42_i10_1_8_cache_$cache.results_$mode ]
        then
            if ! python3 srn.py simulate -i $out_folder/$prob_folder/AIJ_SRN_s42_i10_1_8.experiment -m $mode -e xor -c $cache -o $out_folder/$res_folder/AIJ_SRN_s42_i10_1_8_cache_$cache.results_$mode
            then
                echo "Simulation error on following command:"
                echo python3 srn.py simulate -i $out_folder/$prob_folder/AIJ_SRN_s42_i10_1_8.experiment -m $mode -e xor -c $cache -o $out_folder/$res_folder/AIJ_SRN_s42_i10_1_8_cache_$cache.results_$mode
                echo "Terminated."
                exit 1
            fi
        else
            echo "Results of $mode with cache $cache already exists: skipped..."
        fi
    done
done


# plot results
for mode in WMI-PA WMI-PA-NL
do
    if ! python3 srn.py plot -i $out_folder/$res_folder/AIJ_SRN_s42_i10_1_8_cache_{-1..3}.results_$mode -o $out_folder/$figure_folder/AIJ_SRN_plot
    then
        echo "Plotting error on following command:"
        echo python3 srn.py plot -i $out_folder/$res_folder/AIJ_SRN_s42_i10_1_8_cache_{-1..0}.results_$mode -o $out_folder/$figure_folder/AIJ_SRN_plot
        echo "Terminated."
        exit 1
    fi
done


echo "DONE!"
