
python synthetic.py generate_tree -s 1 -n 10 -b 3 -r 1 -d 2 -o AIJ_TREE_s1_i10_b3_r1_2.experiment
python synthetic.py generate_tree -s 2 -n 10 -b 4 -r 1 -d 2 -o AIJ_TREE_s2_i10_b4_r1_2.experiment
python synthetic.py generate_tree -s 3 -n 10 -b 5 -r 1 -d 2 -o AIJ_TREE_s3_i10_b5_r1_2.experiment
python synthetic.py generate_tree -s 4 -n 10 -b 6 -r 1 -d 2 -o AIJ_TREE_s4_i10_b6_r1_2.experiment

python synthetic.py generate_tree -s 5 -n 10 -b 3 -r 2 -d 2 -o AIJ_TREE_s5_i10_b3_r2_2.experiment
python synthetic.py generate_tree -s 6 -n 10 -b 4 -r 2 -d 2 -o AIJ_TREE_s6_i10_b4_r2_2.experiment
python synthetic.py generate_tree -s 7 -n 10 -b 5 -r 2 -d 2 -o AIJ_TREE_s7_i10_b5_r2_2.experiment
python synthetic.py generate_tree -s 8 -n 10 -b 6 -r 2 -d 2 -o AIJ_TREE_s8_i10_b6_r2_2.experiment

python synthetic.py generate_tree -s 9 -n 10 -b 3 -r 3 -d 2 -o AIJ_TREE_s9_i10_b3_r3_2.experiment
python synthetic.py generate_tree -s 10 -n 10 -b 4 -r 3 -d 2 -o AIJ_TREE_s10_i10_b4_r3_2.experiment
python synthetic.py generate_tree -s 11 -n 10 -b 5 -r 3 -d 2 -o AIJ_TREE_s11_i10_b5_r3_2.experiment
python synthetic.py generate_tree -s 12 -n 10 -b 6 -r 3 -d 2 -o AIJ_TREE_s12_i10_b6_r3_2.experiment

python synthetic.py generate_tree -s 13 -n 10 -b 3 -r 4 -d 2 -o AIJ_TREE_s13_i10_b3_r4_2.experiment
python synthetic.py generate_tree -s 14 -n 10 -b 4 -r 4 -d 2 -o AIJ_TREE_s14_i10_b4_r4_2.experiment
python synthetic.py generate_tree -s 15 -n 10 -b 5 -r 4 -d 2 -o AIJ_TREE_s15_i10_b5_r4_2.experiment
python synthetic.py generate_tree -s 16 -n 10 -b 6 -r 4 -d 2 -o AIJ_TREE_s16_i10_b6_r4_2.experiment

# run WMI-BC
python synthetic.py simulate -i AIJ_TREE_s1_i10_b3_r1_2.experiment -m WMI-BC -o AIJ_TREE_s1_i10_b3_r1_2.results_wmibc
python synthetic.py simulate -i AIJ_TREE_s2_i10_b4_r1_2.experiment -m WMI-BC -o AIJ_TREE_s2_i10_b4_r1_2.results_wmibc
python synthetic.py simulate -i AIJ_TREE_s3_i10_b5_r1_2.experiment -m WMI-BC -o AIJ_TREE_s3_i10_b5_r1_2.results_wmibc
python synthetic.py simulate -i AIJ_TREE_s4_i10_b6_r1_2.experiment -m WMI-BC -o AIJ_TREE_s4_i10_b6_r1_2.results_wmibc

python synthetic.py simulate -i AIJ_TREE_s5_i10_b3_r2_2.experiment -m WMI-BC -o AIJ_TREE_s5_i10_b3_r2_2.results_wmibc
python synthetic.py simulate -i AIJ_TREE_s6_i10_b4_r2_2.experiment -m WMI-BC -o AIJ_TREE_s6_i10_b4_r2_2.results_wmibc
python synthetic.py simulate -i AIJ_TREE_s7_i10_b5_r2_2.experiment -m WMI-BC -o AIJ_TREE_s7_i10_b5_r2_2.results_wmibc
python synthetic.py simulate -i AIJ_TREE_s8_i10_b6_r2_2.experiment -m WMI-BC -o AIJ_TREE_s8_i10_b6_r2_2.results_wmibc

python synthetic.py simulate -i AIJ_TREE_s9_i10_b3_r3_2.experiment -m WMI-BC -o AIJ_TREE_s9_i10_b3_r3_2.results_wmibc
python synthetic.py simulate -i AIJ_TREE_s10_i10_b4_r3_2.experiment -m WMI-BC -o AIJ_TREE_s10_i10_b4_r3_2.results_wmibc
python synthetic.py simulate -i AIJ_TREE_s11_i10_b5_r3_2.experiment -m WMI-BC -o AIJ_TREE_s11_i10_b5_r3_2.results_wmibc
python synthetic.py simulate -i AIJ_TREE_s12_i10_b6_r3_2.experiment -m WMI-BC -o AIJ_TREE_s12_i10_b6_r3_2.results_wmibc

python synthetic.py simulate -i AIJ_TREE_s13_i10_b3_r4_2.experiment -m WMI-BC -o AIJ_TREE_s13_i10_b3_r4_2.results_wmibc
python synthetic.py simulate -i AIJ_TREE_s14_i10_b4_r4_2.experiment -m WMI-BC -o AIJ_TREE_s14_i10_b4_r4_2.results_wmibc
python synthetic.py simulate -i AIJ_TREE_s15_i10_b5_r4_2.experiment -m WMI-BC -o AIJ_TREE_s15_i10_b5_r4_2.results_wmibc
python synthetic.py simulate -i AIJ_TREE_s16_i10_b6_r4_2.experiment -m WMI-BC -o AIJ_TREE_s16_i10_b6_r4_2.results_wmibc

# run WMI-ALLSMT
python synthetic.py simulate -i AIJ_TREE_s1_i10_b3_r1_2.experiment -m WMI-ALLSMT -o AIJ_TREE_s1_i10_b3_r1_2.results_wmiallsmt
python synthetic.py simulate -i AIJ_TREE_s2_i10_b4_r1_2.experiment -m WMI-ALLSMT -o AIJ_TREE_s2_i10_b4_r1_2.results_wmiallsmt
python synthetic.py simulate -i AIJ_TREE_s3_i10_b5_r1_2.experiment -m WMI-ALLSMT -o AIJ_TREE_s3_i10_b5_r1_2.results_wmiallsmt
python synthetic.py simulate -i AIJ_TREE_s4_i10_b6_r1_2.experiment -m WMI-ALLSMT -o AIJ_TREE_s4_i10_b6_r1_2.results_wmiallsmt

python synthetic.py simulate -i AIJ_TREE_s5_i10_b3_r2_2.experiment -m WMI-ALLSMT -o AIJ_TREE_s5_i10_b3_r2_2.results_wmiallsmt
python synthetic.py simulate -i AIJ_TREE_s6_i10_b4_r2_2.experiment -m WMI-ALLSMT -o AIJ_TREE_s6_i10_b4_r2_2.results_wmiallsmt
python synthetic.py simulate -i AIJ_TREE_s7_i10_b5_r2_2.experiment -m WMI-ALLSMT -o AIJ_TREE_s7_i10_b5_r2_2.results_wmiallsmt
python synthetic.py simulate -i AIJ_TREE_s8_i10_b6_r2_2.experiment -m WMI-ALLSMT -o AIJ_TREE_s8_i10_b6_r2_2.results_wmiallsmt

python synthetic.py simulate -i AIJ_TREE_s9_i10_b3_r3_2.experiment -m WMI-ALLSMT -o AIJ_TREE_s9_i10_b3_r3_2.results_wmiallsmt
python synthetic.py simulate -i AIJ_TREE_s10_i10_b4_r3_2.experiment -m WMI-ALLSMT -o AIJ_TREE_s10_i10_b4_r3_2.results_wmiallsmt
python synthetic.py simulate -i AIJ_TREE_s11_i10_b5_r3_2.experiment -m WMI-ALLSMT -o AIJ_TREE_s11_i10_b5_r3_2.results_wmiallsmt
python synthetic.py simulate -i AIJ_TREE_s12_i10_b6_r3_2.experiment -m WMI-ALLSMT -o AIJ_TREE_s12_i10_b6_r3_2.results_wmiallsmt

python synthetic.py simulate -i AIJ_TREE_s13_i10_b3_r4_2.experiment -m WMI-ALLSMT -o AIJ_TREE_s13_i10_b3_r4_2.results_wmiallsmt
python synthetic.py simulate -i AIJ_TREE_s14_i10_b4_r4_2.experiment -m WMI-ALLSMT -o AIJ_TREE_s14_i10_b4_r4_2.results_wmiallsmt
python synthetic.py simulate -i AIJ_TREE_s15_i10_b5_r4_2.experiment -m WMI-ALLSMT -o AIJ_TREE_s15_i10_b5_r4_2.results_wmiallsmt
python synthetic.py simulate -i AIJ_TREE_s16_i10_b6_r4_2.experiment -m WMI-ALLSMT -o AIJ_TREE_s16_i10_b6_r4_2.results_wmiallsmt

# run WMI-PA
python synthetic.py simulate -i AIJ_TREE_s1_i10_b3_r1_2.experiment -m WMI-PA -o AIJ_TREE_s1_i10_b3_r1_2.results_wmipa
python synthetic.py simulate -i AIJ_TREE_s2_i10_b4_r1_2.experiment -m WMI-PA -o AIJ_TREE_s2_i10_b4_r1_2.results_wmipa
python synthetic.py simulate -i AIJ_TREE_s3_i10_b5_r1_2.experiment -m WMI-PA -o AIJ_TREE_s3_i10_b5_r1_2.results_wmipa
python synthetic.py simulate -i AIJ_TREE_s4_i10_b6_r1_2.experiment -m WMI-PA -o AIJ_TREE_s4_i10_b6_r1_2.results_wmipa

python synthetic.py simulate -i AIJ_TREE_s5_i10_b3_r2_2.experiment -m WMI-PA -o AIJ_TREE_s5_i10_b3_r2_2.results_wmipa
python synthetic.py simulate -i AIJ_TREE_s6_i10_b4_r2_2.experiment -m WMI-PA -o AIJ_TREE_s6_i10_b4_r2_2.results_wmipa
python synthetic.py simulate -i AIJ_TREE_s7_i10_b5_r2_2.experiment -m WMI-PA -o AIJ_TREE_s7_i10_b5_r2_2.results_wmipa
python synthetic.py simulate -i AIJ_TREE_s8_i10_b6_r2_2.experiment -m WMI-PA -o AIJ_TREE_s8_i10_b6_r2_2.results_wmipa

python synthetic.py simulate -i AIJ_TREE_s9_i10_b3_r3_2.experiment -m WMI-PA -o AIJ_TREE_s9_i10_b3_r3_2.results_wmipa
python synthetic.py simulate -i AIJ_TREE_s10_i10_b4_r3_2.experiment -m WMI-PA -o AIJ_TREE_s10_i10_b4_r3_2.results_wmipa
python synthetic.py simulate -i AIJ_TREE_s11_i10_b5_r3_2.experiment -m WMI-PA -o AIJ_TREE_s11_i10_b5_r3_2.results_wmipa
python synthetic.py simulate -i AIJ_TREE_s12_i10_b6_r3_2.experiment -m WMI-PA -o AIJ_TREE_s12_i10_b6_r3_2.results_wmipa

python synthetic.py simulate -i AIJ_TREE_s13_i10_b3_r4_2.experiment -m WMI-PA -o AIJ_TREE_s13_i10_b3_r4_2.results_wmipa
python synthetic.py simulate -i AIJ_TREE_s14_i10_b4_r4_2.experiment -m WMI-PA -o AIJ_TREE_s14_i10_b4_r4_2.results_wmipa
python synthetic.py simulate -i AIJ_TREE_s15_i10_b5_r4_2.experiment -m WMI-PA -o AIJ_TREE_s15_i10_b5_r4_2.results_wmipa
python synthetic.py simulate -i AIJ_TREE_s16_i10_b6_r4_2.experiment -m WMI-PA -o AIJ_TREE_s16_i10_b6_r4_2.results_wmipa

# run PRAiSE
python synthetic.py simulate -i AIJ_TREE_s1_i10_b3_r1_2.experiment -m PRAiSE -o AIJ_TREE_s1_i10_b3_r1_2.results_praise
python synthetic.py simulate -i AIJ_TREE_s2_i10_b4_r1_2.experiment -m PRAiSE -o AIJ_TREE_s2_i10_b4_r1_2.results_praise
python synthetic.py simulate -i AIJ_TREE_s3_i10_b5_r1_2.experiment -m PRAiSE -o AIJ_TREE_s3_i10_b5_r1_2.results_praise
python synthetic.py simulate -i AIJ_TREE_s4_i10_b6_r1_2.experiment -m PRAiSE -o AIJ_TREE_s4_i10_b6_r1_2.results_praise

python synthetic.py simulate -i AIJ_TREE_s5_i10_b3_r2_2.experiment -m PRAiSE -o AIJ_TREE_s5_i10_b3_r2_2.results_praise
python synthetic.py simulate -i AIJ_TREE_s6_i10_b4_r2_2.experiment -m PRAiSE -o AIJ_TREE_s6_i10_b4_r2_2.results_praise
python synthetic.py simulate -i AIJ_TREE_s7_i10_b5_r2_2.experiment -m PRAiSE -o AIJ_TREE_s7_i10_b5_r2_2.results_praise
python synthetic.py simulate -i AIJ_TREE_s8_i10_b6_r2_2.experiment -m PRAiSE -o AIJ_TREE_s8_i10_b6_r2_2.results_praise

python synthetic.py simulate -i AIJ_TREE_s9_i10_b3_r3_2.experiment -m PRAiSE -o AIJ_TREE_s9_i10_b3_r3_2.results_praise
python synthetic.py simulate -i AIJ_TREE_s10_i10_b4_r3_2.experiment -m PRAiSE -o AIJ_TREE_s10_i10_b4_r3_2.results_praise
python synthetic.py simulate -i AIJ_TREE_s11_i10_b5_r3_2.experiment -m PRAiSE -o AIJ_TREE_s11_i10_b5_r3_2.results_praise
python synthetic.py simulate -i AIJ_TREE_s12_i10_b6_r3_2.experiment -m PRAiSE -o AIJ_TREE_s12_i10_b6_r3_2.results_praise

python synthetic.py simulate -i AIJ_TREE_s13_i10_b3_r4_2.experiment -m PRAiSE -o AIJ_TREE_s13_i10_b3_r4_2.results_praise
python synthetic.py simulate -i AIJ_TREE_s14_i10_b4_r4_2.experiment -m PRAiSE -o AIJ_TREE_s14_i10_b4_r4_2.results_praise
python synthetic.py simulate -i AIJ_TREE_s15_i10_b5_r4_2.experiment -m PRAiSE -o AIJ_TREE_s15_i10_b5_r4_2.results_praise
python synthetic.py simulate -i AIJ_TREE_s16_i10_b6_r4_2.experiment -m PRAiSE -o AIJ_TREE_s16_i10_b6_r4_2.results_praise

# run XADD
python synthetic.py simulate -i AIJ_TREE_s1_i10_b3_r1_2.experiment -m XADD -o AIJ_TREE_s1_i10_b3_r1_2.results_xadd
python synthetic.py simulate -i AIJ_TREE_s2_i10_b4_r1_2.experiment -m XADD -o AIJ_TREE_s2_i10_b4_r1_2.results_xadd
python synthetic.py simulate -i AIJ_TREE_s3_i10_b5_r1_2.experiment -m XADD -o AIJ_TREE_s3_i10_b5_r1_2.results_xadd
python synthetic.py simulate -i AIJ_TREE_s4_i10_b6_r1_2.experiment -m XADD -o AIJ_TREE_s4_i10_b6_r1_2.results_xadd

python synthetic.py simulate -i AIJ_TREE_s5_i10_b3_r2_2.experiment -m XADD -o AIJ_TREE_s5_i10_b3_r2_2.results_xadd
python synthetic.py simulate -i AIJ_TREE_s6_i10_b4_r2_2.experiment -m XADD -o AIJ_TREE_s6_i10_b4_r2_2.results_xadd
python synthetic.py simulate -i AIJ_TREE_s7_i10_b5_r2_2.experiment -m XADD -o AIJ_TREE_s7_i10_b5_r2_2.results_xadd
python synthetic.py simulate -i AIJ_TREE_s8_i10_b6_r2_2.experiment -m XADD -o AIJ_TREE_s8_i10_b6_r2_2.results_xadd

python synthetic.py simulate -i AIJ_TREE_s9_i10_b3_r3_2.experiment -m XADD -o AIJ_TREE_s9_i10_b3_r3_2.results_xadd
python synthetic.py simulate -i AIJ_TREE_s10_i10_b4_r3_2.experiment -m XADD -o AIJ_TREE_s10_i10_b4_r3_2.results_xadd
python synthetic.py simulate -i AIJ_TREE_s11_i10_b5_r3_2.experiment -m XADD -o AIJ_TREE_s11_i10_b5_r3_2.results_xadd
python synthetic.py simulate -i AIJ_TREE_s12_i10_b6_r3_2.experiment -m XADD -o AIJ_TREE_s12_i10_b6_r3_2.results_xadd

python synthetic.py simulate -i AIJ_TREE_s13_i10_b3_r4_2.experiment -m XADD -o AIJ_TREE_s13_i10_b3_r4_2.results_xadd
python synthetic.py simulate -i AIJ_TREE_s14_i10_b4_r4_2.experiment -m XADD -o AIJ_TREE_s14_i10_b4_r4_2.results_xadd
python synthetic.py simulate -i AIJ_TREE_s15_i10_b5_r4_2.experiment -m XADD -o AIJ_TREE_s15_i10_b5_r4_2.results_xadd
python synthetic.py simulate -i AIJ_TREE_s16_i10_b6_r4_2.experiment -m XADD -o AIJ_TREE_s16_i10_b6_r4_2.results_xadd


# plots
python synthetic.py plot -i AIJ_TREE_s*.results_{xadd,praise,wmibc,wmiallsmt,wmipa} -o AIJ_TREE_plot
