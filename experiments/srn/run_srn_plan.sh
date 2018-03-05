
if [ ! -e data/MAR15.csv ]
then
    cd data
    gunzip MAR15.csv.tar.gz
    tar -xf MAR15.csv.tar
    cd ..
fi

python srnplan.py generate -i data/MAR15.csv -s 42 --iterations=10 --min-length=1 --max-length=1 -o AIJ_PLAN_s42_i10_1_1.experiment
python srnplan.py generate -i data/MAR15.csv -s 42 --iterations=10 --min-length=2 --max-length=2 -o AIJ_PLAN_s42_i10_2_2.experiment
python srnplan.py generate -i data/MAR15.csv -s 42 --iterations=10 --min-length=3 --max-length=3 -o AIJ_PLAN_s42_i10_3_3.experiment
python srnplan.py generate -i data/MAR15.csv -s 42 --iterations=10 --min-length=4 --max-length=4 -o AIJ_PLAN_s42_i10_4_4.experiment
python srnplan.py generate -i data/MAR15.csv -s 42 --iterations=10 --min-length=5 --max-length=5 -o AIJ_PLAN_s42_i10_5_5.experiment
python srnplan.py generate -i data/MAR15.csv -s 42 --iterations=10 --min-length=6 --max-length=6 -o AIJ_PLAN_s42_i10_6_6.experiment
python srnplan.py generate -i data/MAR15.csv -s 42 --iterations=10 --min-length=7 --max-length=7 -o AIJ_PLAN_s42_i10_7_7.experiment
python srnplan.py generate -i data/MAR15.csv -s 42 --iterations=10 --min-length=8 --max-length=8 -o AIJ_PLAN_s42_i10_8_8.experiment

# run WMI-PA
python srnplan.py simulate -i AIJ_PLAN_s42_i10_1_1.experiment -m WMI-PA -e xor -o AIJ_PLAN_s42_i10_1_1.results_wmipa
python srnplan.py simulate -i AIJ_PLAN_s42_i10_2_2.experiment -m WMI-PA -e xor -o AIJ_PLAN_s42_i10_2_2.results_wmipa
python srnplan.py simulate -i AIJ_PLAN_s42_i10_3_3.experiment -m WMI-PA -e xor -o AIJ_PLAN_s42_i10_3_3.results_wmipa
python srnplan.py simulate -i AIJ_PLAN_s42_i10_4_4.experiment -m WMI-PA -e xor -o AIJ_PLAN_s42_i10_4_4.results_wmipa
python srnplan.py simulate -i AIJ_PLAN_s42_i10_5_5.experiment -m WMI-PA -e xor -o AIJ_PLAN_s42_i10_5_5.results_wmipa
python srnplan.py simulate -i AIJ_PLAN_s42_i10_6_6.experiment -m WMI-PA -e xor -o AIJ_PLAN_s42_i10_6_6.results_wmipa
python srnplan.py simulate -i AIJ_PLAN_s42_i10_7_7.experiment -m WMI-PA -e xor -o AIJ_PLAN_s42_i10_7_7.results_wmipa
python srnplan.py simulate -i AIJ_PLAN_s42_i10_8_8.experiment -m WMI-PA -e xor -o AIJ_PLAN_s42_i10_8_8.results_wmipa

# run PRAiSE
python srnplan.py simulate -i AIJ_PLAN_s42_i10_1_1.experiment -m PRAiSE -e xor -o AIJ_PLAN_s42_i10_1_1.results_praise
python srnplan.py simulate -i AIJ_PLAN_s42_i10_2_2.experiment -m PRAiSE -e xor -o AIJ_PLAN_s42_i10_2_2.results_praise
python srnplan.py simulate -i AIJ_PLAN_s42_i10_3_3.experiment -m PRAiSE -e xor -o AIJ_PLAN_s42_i10_3_3.results_praise
python srnplan.py simulate -i AIJ_PLAN_s42_i10_4_4.experiment -m PRAiSE -e xor -o AIJ_PLAN_s42_i10_4_4.results_praise
python srnplan.py simulate -i AIJ_PLAN_s42_i10_5_5.experiment -m PRAiSE -e xor -o AIJ_PLAN_s42_i10_5_5.results_praise
python srnplan.py simulate -i AIJ_PLAN_s42_i10_6_6.experiment -m PRAiSE -e xor -o AIJ_PLAN_s42_i10_6_6.results_praise
python srnplan.py simulate -i AIJ_PLAN_s42_i10_7_7.experiment -m PRAiSE -e xor -o AIJ_PLAN_s42_i10_7_7.results_praise
python srnplan.py simulate -i AIJ_PLAN_s42_i10_8_8.experiment -m PRAiSE -e xor -o AIJ_PLAN_s42_i10_8_8.results_praise

# plot
python srnplan.py plot -i AIJ_PLAN_s42_i10_{1_1,2_2,3_3,4_4,5_5,6_6,7_7,8_8}.results_{wmipa,praise} -o AIJ_PLAN_plot
