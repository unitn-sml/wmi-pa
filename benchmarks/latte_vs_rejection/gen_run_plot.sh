
#!/bin/bash

TIMEOUT=600 # seconds
#NINSTANCES=10

#MINREALS=3
#MAXREALS=8

INPUT_DIR="./input/"
OUTPUT_DIR="./output/"


mkdir $INPUT_DIR
#for NREALS in $(seq $MINREALS $MAXREALS)
#do
#    for ID in $(seq 1 $NINSTANCES)
#    do
#	python3 ../synthetic.py $ID --directory $INPUT_DIR --n_reals $NREALS
#    done
#done
mkdir $OUTPUT_DIR

OLDPA_DIR=$OUTPUT_DIR"oldpa/"
mkdir $OLDPA_DIR
for FILENAME in $(ls $INPUT_DIR)
do
    echo "Computing "$FILENAME" with latte"
    timeout $TIMEOUT python3 ../../wmipa/cli/cli.py $INPUT_DIR$FILENAME > $OLDPA_DIR$FILENAME
done

# manually removing tmp directories left by processed that timed out
rm -r tmp* 2> /dev/null

