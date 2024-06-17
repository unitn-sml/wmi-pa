# Experimental setting for UAI / AIJ 2022

## Synthetic experiments
* Generate synthetic experiments by running
      
      ./synthetic_gen.py

  This script generates the random problems in ./synthetic_exp/data

* The problems can then be evaluated by running
    
      ./synthetic_eval.sh
  
  Experimental results are saved in ./synthetic_exp/results

* Finally, plots can be generated with
    
      ./synthetic_plot.sh

  Plots are saved in ./synthetic_exp/plots

## Density estimation trees (DET)
This set of problems has been generated using the code in  [this repository](https://github.com/paolomorettin/hybrid-benchmarks).
* Generate DETs by running
      
      ./mlc_gen.py

  This script generates the random problems in ./mlc/data

* The problems can then be evaluated by running
    
      ./mlc_eval.sh
  
  Experimental results are saved in ./mlc/results

* Finally, plots can be generated with
    
      ./mlc_plot.sh

  Plots are saved in ./mlc/plots

