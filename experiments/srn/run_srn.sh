
python srn.py simulate -i data/MAR15.csv --iterations=5 --max-length=6 -o results_srn.csv
python srn.py plot -i results_srn.csv -o plot_srn.png
