
#!/bin/bash

TIMEOUT=600 # seconds
NINSTANCES=20

MINREALS=2
MAXREALS=10

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
for FILENAME in $(ls $INPUT_DIR)
do
    echo "Computing "$FILENAME" with latte"
    timeout $TIMEOUT python3 ../../wmipa/cli/cli.py $INPUT_DIR$FILENAME latte > $LATTE_DIR$FILENAME
done

REJ_DIR=$OUTPUT_DIR"rej/"
mkdir $REJ_DIR
for FILENAME in $(ls $INPUT_DIR)
do
    echo "Computing "$FILENAME" with rejection"
    timeout $TIMEOUT python3 ../../wmipa/cli/cli.py $INPUT_DIR$FILENAME rejection > $REJ_DIR$FILENAME
done

# manually removing tmp directories left by processed that timed out
rm -r tmp* 2> /dev/null

