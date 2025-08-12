
#!/bin/bash

TIMEOUT=600 # seconds
NINSTANCES=20
NQUERIES=5

MINREALS=3
MAXREALS=7

INPUT_DIR="./input/"
OUTPUT_DIR="./output/"


mkdir $INPUT_DIR
for NREALS in $(seq $MINREALS $MAXREALS)
do
    for ID in $(seq 1 $NINSTANCES)
    do
	python3 ../synthetic.py $ID --directory $INPUT_DIR --n_reals $NREALS --n_queries $NQUERIES
    done
done

mkdir $OUTPUT_DIR
NOCACHE_DIR=$OUTPUT_DIR"nocache/"
mkdir $NOCACHE_DIR
CACHE_DIR=$OUTPUT_DIR"cache/"
mkdir $CACHE_DIR

for FILENAME in $(ls $INPUT_DIR)
do
    RESULTS=$NOCACHE_DIR$FILENAME
    if [ -f $RESULTS ]
    then
	echo "Skipping "$FILENAME" with latte"
    else
	echo "Computing "$FILENAME" with latte"
	timeout $TIMEOUT wmipa run $INPUT_DIR$FILENAME --integrator latte > $RESULTS
    fi
    
    RESULTS=$CACHE_DIR$FILENAME
    if [ -f $RESULTS ]
    then
	echo "Skipping "$FILENAME" with latte+cache"
    else
	echo "Computing "$FILENAME" with latte+cache"
	timeout $TIMEOUT wmipa run $INPUT_DIR$FILENAME --integrator cache-latte > $RESULTS
    fi
done

# manually removing tmp directories left by processed that timed out
rm -r tmp* 2> /dev/null

XPATHS=$CACHE_DIR"*"
YPATHS=$NOCACHE_DIR"*"
python3 ../plot.py --logscale --xlabel "cache+latte" --ylabel "latte" runtime-scatter --xpaths $XPATHS --ypaths $YPATHS --timeout $TIMEOUT
