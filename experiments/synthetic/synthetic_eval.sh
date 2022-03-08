SYN_DIR=synthetic_exp

for dir in $(ls $SYN_DIR/data)
do
	mkdir $SYN_DIR/results/$dir
	echo Evaluating $dir
	for mode in SAPA PA
	do
		echo Mode $mode
		python3 evaluateModels.py $SYN_DIR/data/$dir -o $SYN_DIR/results/$dir -m $mode 
	done
done
