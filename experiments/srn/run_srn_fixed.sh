
if [ ! -e data/MAR15.csv ]
then
    cd data
    gunzip MAR15.csv.tar.gz
    tar -xf MAR15.csv.tar
    cd ..
fi

python srn.py generate -i data/MAR15.csv -s 42 --iterations=10 --min-length=1 --max-length=6 -o AIJ_SRN_s42_i10_1_6.experiment
python srn.py generate -i data/MAR15.csv -s 42 --iterations=10 --min-length=7 --max-length=8 -o AIJ_SRN_s42_i10_7_8.experiment

# run WMI-BC
python srn.py simulate -i AIJ_SRN_s42_i10_1_6.experiment -m WMI-BC -e xor -o AIJ_SRN_s42_i10_1_6.results_wmibc
python srn.py simulate -i AIJ_SRN_s42_i10_7_8.experiment -m WMI-BC -e xor -o AIJ_SRN_s42_i10_7_8.results_wmibc

# run WMI-ALLSMT
python srn.py simulate -i AIJ_SRN_s42_i10_1_6.experiment -m WMI-ALLSMT -e xor -o AIJ_SRN_s42_i10_1_6.results_wmiallsmt
python srn.py simulate -i AIJ_SRN_s42_i10_7_8.experiment -m WMI-ALLSMT -e xor -o AIJ_SRN_s42_i10_7_8.results_wmiallsmt

# run WMI-PA
python srn.py simulate -i AIJ_SRN_s42_i10_1_6.experiment -m WMI-PA -e xor -o AIJ_SRN_s42_i10_1_6.results_wmipa
python srn.py simulate -i AIJ_SRN_s42_i10_7_8.experiment -m WMI-PA -e xor -o AIJ_SRN_s42_i10_7_8.results_wmipa

# run PRAiSE
python srn.py simulate -i AIJ_SRN_s42_i10_1_6.experiment -m PRAiSE -e xor -o AIJ_SRN_s42_i10_1_6.results_praise
python srn.py simulate -i AIJ_SRN_s42_i10_7_8.experiment -m PRAiSE -e xor -o AIJ_SRN_s42_i10_7_8.results_praise

# plot
python srn.py plot -i AIJ_SRN_s42_i10_{1_6,7_8}.results_{praise,wmibc,wmiallsmt,wmipa} -o AIJ_SRN_plot





