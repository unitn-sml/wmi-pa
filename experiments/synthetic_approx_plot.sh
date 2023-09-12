#!/bin/bash

SYN_DIR=synthetic_exp
RES_DIR=$SYN_DIR/results_approx
PLT_DIR=$SYN_DIR/plots_approx

mkdir -p $PLT_DIR



# fix nreals to 3
python3 plot_approx.py $RES_DIR/ --output $PLT_DIR/ --filename "_e0.01_nreals_3" -o $PLT_DIR/ --fix integrator_error=0.01 nreals=3 --rows-var pd --cols-var integrator_N
python3 plot_approx.py $RES_DIR/ --output $PLT_DIR/ --filename "_e0.01_degree_4" -o $PLT_DIR/ --fix integrator_error=0.01 pd=4 --rows-var nreals --cols-var integrator_N


python3 plot_approx.py $RES_DIR/ --output $PLT_DIR/ --filename "_N1000_nreals_3" -o $PLT_DIR/ --fix integrator_N=1000 nreals=3 --rows-var pd --cols-var integrator_error
python3 plot_approx.py $RES_DIR/ --output $PLT_DIR/ --filename "_N1000_degree_4" -o $PLT_DIR/ --fix integrator_N=1000 pd=4 --rows-var nreals --cols-var integrator_error
