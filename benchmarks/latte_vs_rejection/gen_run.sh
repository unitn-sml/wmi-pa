
#!/bin/bash

TIMEOUT=600 # seconds
NINSTANCES=20

MINREALS=3
MAXREALS=7

INPUT_DIR="./input/"
OUTPUT_DIR="./output/"


mkdir $INPUT_DIR
for NREALS in $(seq $MINREALS $MAXREALS)
do
    for ID in $(seq 1 $NINSTANCES)
    do
	python3 ../synthetic.py $ID --directory $INPUT_DIR --n_reals $NREALS
    done
done

mkdir $OUTPUT_DIR
LATTE_DIR=$OUTPUT_DIR"latte/"
mkdir $LATTE_DIR
REJ_DIR=$OUTPUT_DIR"rej/"
mkdir $REJ_DIR

for FILENAME in $(ls $INPUT_DIR)
do
    RESULTS=$LATTE_DIR$FILENAME
    if [ -f $RESULTS ]
    then
	echo "Skipping "$FILENAME" with latte"
    else
	echo "Computing "$FILENAME" with latte"
	timeout $TIMEOUT wmipa run $INPUT_DIR$FILENAME --integrator latte > $RESULTS
    fi
    
    RESULTS=$REJ_DIR$FILENAME
    if [ -f $RESULTS ]
    then
	echo "Skipping "$FILENAME" with rejection"
    else	
	echo "Computing "$FILENAME" with rejection"
	timeout $TIMEOUT wmipa run $INPUT_DIR$FILENAME --integrator rejection > $REJ_DIR$FILENAME
    fi
done

# manually removing tmp directories left by processed that timed out
rm -r tmp* 2> /dev/null

XPATHS=$REJ_DIR"*"
YPATHS=$LATTE_DIR"*"
python3 ../plot.py --logscale --xlabel "rejection" --ylabel "latte" runtime-scatter --xpaths $XPATHS --ypaths $YPATHS --timeout $TIMEOUT

