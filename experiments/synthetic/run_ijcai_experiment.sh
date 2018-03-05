
python synthetic.py generate_ijcai17 -s 42 -n 10 -b 5 -r 2 --n_conj 4 --n_disj 4 -o AIJ_IJCAI_s42_i10_b5_r2_4_4.experiment
python synthetic.py generate_ijcai17 -s 42 -n 10 -b 5 -r 2 --n_conj 5 --n_disj 5 -o AIJ_IJCAI_s42_i10_b5_r2_5_5.experiment
python synthetic.py generate_ijcai17 -s 42 -n 10 -b 5 -r 3 --n_conj 4 --n_disj 4 -o AIJ_IJCAI_s42_i10_b5_r3_4_4.experiment
python synthetic.py generate_ijcai17 -s 42 -n 10 -b 5 -r 3 --n_conj 5 --n_disj 5 -o AIJ_IJCAI_s42_i10_b5_r3_5_5.experiment
python synthetic.py generate_ijcai17 -s 42 -n 10 -b 6 -r 2 --n_conj 4 --n_disj 4 -o AIJ_IJCAI_s42_i10_b6_r2_4_4.experiment
python synthetic.py generate_ijcai17 -s 42 -n 10 -b 6 -r 2 --n_conj 5 --n_disj 5 -o AIJ_IJCAI_s42_i10_b6_r2_5_5.experiment
python synthetic.py generate_ijcai17 -s 42 -n 10 -b 6 -r 3 --n_conj 4 --n_disj 4 -o AIJ_IJCAI_s42_i10_b6_r3_4_4.experiment
python synthetic.py generate_ijcai17 -s 42 -n 10 -b 6 -r 3 --n_conj 5 --n_disj 5 -o AIJ_IJCAI_s42_i10_b6_r3_5_5.experiment
python synthetic.py generate_ijcai17 -s 42 -n 10 -b 7 -r 2 --n_conj 4 --n_disj 4 -o AIJ_IJCAI_s42_i10_b7_r2_4_4.experiment
python synthetic.py generate_ijcai17 -s 42 -n 10 -b 7 -r 2 --n_conj 5 --n_disj 5 -o AIJ_IJCAI_s42_i10_b7_r2_5_5.experiment

# running WMI-BC
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r2_4_4.experiment -m WMI-BC -o AIJ_IJCAI_s42_i10_b5_r2_4_4.results_wmibc
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r2_5_5.experiment -m WMI-BC -o AIJ_IJCAI_s42_i10_b5_r2_5_5.results_wmibc
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r3_4_4.experiment -m WMI-BC -o AIJ_IJCAI_s42_i10_b5_r3_4_4.results_wmibc
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r3_5_5.experiment -m WMI-BC -o AIJ_IJCAI_s42_i10_b5_r3_5_5.results_wmibc
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r2_4_4.experiment -m WMI-BC -o AIJ_IJCAI_s42_i10_b6_r2_4_4.results_wmibc
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r2_5_5.experiment -m WMI-BC -o AIJ_IJCAI_s42_i10_b6_r2_5_5.results_wmibc
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r3_4_4.experiment -m WMI-BC -o AIJ_IJCAI_s42_i10_b6_r3_4_4.results_wmibc
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r3_5_5.experiment -m WMI-BC -o AIJ_IJCAI_s42_i10_b6_r3_5_5.results_wmibc
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b7_r2_4_4.experiment -m WMI-BC -o AIJ_IJCAI_s42_i10_b7_r2_4_4.results_wmibc
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b7_r2_5_5.experiment -m WMI-BC -o AIJ_IJCAI_s42_i10_b7_r2_5_5.results_wmibc

# running WMI-ALLSMT
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r2_4_4.experiment -m WMI-ALLSMT -o AIJ_IJCAI_s42_i10_b5_r2_4_4.results_wmiallsmt
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r2_5_5.experiment -m WMI-ALLSMT -o AIJ_IJCAI_s42_i10_b5_r2_5_5.results_wmiallsmt
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r3_4_4.experiment -m WMI-ALLSMT -o AIJ_IJCAI_s42_i10_b5_r3_4_4.results_wmiallsmt
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r3_5_5.experiment -m WMI-ALLSMT -o AIJ_IJCAI_s42_i10_b5_r3_5_5.results_wmiallsmt
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r2_4_4.experiment -m WMI-ALLSMT -o AIJ_IJCAI_s42_i10_b6_r2_4_4.results_wmiallsmt
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r2_5_5.experiment -m WMI-ALLSMT -o AIJ_IJCAI_s42_i10_b6_r2_5_5.results_wmiallsmt
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r3_4_4.experiment -m WMI-ALLSMT -o AIJ_IJCAI_s42_i10_b6_r3_4_4.results_wmiallsmt
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r3_5_5.experiment -m WMI-ALLSMT -o AIJ_IJCAI_s42_i10_b6_r3_5_5.results_wmiallsmt
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b7_r2_4_4.experiment -m WMI-ALLSMT -o AIJ_IJCAI_s42_i10_b7_r2_4_4.results_wmiallsmt
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b7_r2_5_5.experiment -m WMI-ALLSMT -o AIJ_IJCAI_s42_i10_b7_r2_5_5.results_wmiallsmt

# running WMI-PA
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r2_4_4.experiment -m WMI-PA -o AIJ_IJCAI_s42_i10_b5_r2_4_4.results_wmipa
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r2_5_5.experiment -m WMI-PA -o AIJ_IJCAI_s42_i10_b5_r2_5_5.results_wmipa
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r3_4_4.experiment -m WMI-PA -o AIJ_IJCAI_s42_i10_b5_r3_4_4.results_wmipa
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r3_5_5.experiment -m WMI-PA -o AIJ_IJCAI_s42_i10_b5_r3_5_5.results_wmipa
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r2_4_4.experiment -m WMI-PA -o AIJ_IJCAI_s42_i10_b6_r2_4_4.results_wmipa
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r2_5_5.experiment -m WMI-PA -o AIJ_IJCAI_s42_i10_b6_r2_5_5.results_wmipa
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r3_4_4.experiment -m WMI-PA -o AIJ_IJCAI_s42_i10_b6_r3_4_4.results_wmipa
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r3_5_5.experiment -m WMI-PA -o AIJ_IJCAI_s42_i10_b6_r3_5_5.results_wmipa
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b7_r2_4_4.experiment -m WMI-PA -o AIJ_IJCAI_s42_i10_b7_r2_4_4.results_wmipa
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b7_r2_5_5.experiment -m WMI-PA -o AIJ_IJCAI_s42_i10_b7_r2_5_5.results_wmipa

# running PRAiSE
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r2_4_4.experiment -m PRAiSE -o AIJ_IJCAI_s42_i10_b5_r2_4_4.results_praise
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r2_5_5.experiment -m PRAiSE -o AIJ_IJCAI_s42_i10_b5_r2_5_5.results_praise
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r3_4_4.experiment -m PRAiSE -o AIJ_IJCAI_s42_i10_b5_r3_4_4.results_praise
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r3_5_5.experiment -m PRAiSE -o AIJ_IJCAI_s42_i10_b5_r3_5_5.results_praise
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r2_4_4.experiment -m PRAiSE -o AIJ_IJCAI_s42_i10_b6_r2_4_4.results_praise
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r2_5_5.experiment -m PRAiSE -o AIJ_IJCAI_s42_i10_b6_r2_5_5.results_praise
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r3_4_4.experiment -m PRAiSE -o AIJ_IJCAI_s42_i10_b6_r3_4_4.results_praise
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r3_5_5.experiment -m PRAiSE -o AIJ_IJCAI_s42_i10_b6_r3_5_5.results_praise
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b7_r2_4_4.experiment -m PRAiSE -o AIJ_IJCAI_s42_i10_b7_r2_4_4.results_praise
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b7_r2_5_5.experiment -m PRAiSE -o AIJ_IJCAI_s42_i10_b7_r2_5_5.results_praise

# running XADD
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r2_4_4.experiment -m XADD -o AIJ_IJCAI_s42_i10_b5_r2_4_4.results_xadd
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r2_5_5.experiment -m XADD -o AIJ_IJCAI_s42_i10_b5_r2_5_5.results_xadd
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r3_4_4.experiment -m XADD -o AIJ_IJCAI_s42_i10_b5_r3_4_4.results_xadd
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b5_r3_5_5.experiment -m XADD -o AIJ_IJCAI_s42_i10_b5_r3_5_5.results_xadd
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r2_4_4.experiment -m XADD -o AIJ_IJCAI_s42_i10_b6_r2_4_4.results_xadd
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r2_5_5.experiment -m XADD -o AIJ_IJCAI_s42_i10_b6_r2_5_5.results_xadd
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r3_4_4.experiment -m XADD -o AIJ_IJCAI_s42_i10_b6_r3_4_4.results_xadd
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b6_r3_5_5.experiment -m XADD -o AIJ_IJCAI_s42_i10_b6_r3_5_5.results_xadd
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b7_r2_4_4.experiment -m XADD -o AIJ_IJCAI_s42_i10_b7_r2_4_4.results_xadd
python synthetic.py simulate -i AIJ_IJCAI_s42_i10_b7_r2_5_5.experiment -m XADD -o AIJ_IJCAI_s42_i10_b7_r2_5_5.results_xadd

# plots
python synthetic.py plot -i AIJ_IJCAI_s42_*.results_{xadd,praise,wmibc,wmiallsmt,wmipa} -o AIJ_IJCAI_plot


