
#!/bin/bash

TIMEOUT=120 # seconds
NINSTANCES=10
NREALS=7

INPUT_DIR="./input/"
OUTPUT_DIR="./output/"


##### GENERATE
mkdir $INPUT_DIR
for ID in $(seq 1 $NINSTANCES)
do
    python3 ../synthetic.py $ID --directory $INPUT_DIR --n_reals $NREALS
done

mkdir $OUTPUT_DIR

##### RUN
LATTE_DIR=$OUTPUT_DIR"latte/"
mkdir $LATTE_DIR
for FILENAME in $(ls $INPUT_DIR)
do
    echo "Computing "$FILENAME" with latte"
    timeout $TIMEOUT wmipa run $INPUT_DIR$FILENAME latte > $LATTE_DIR$FILENAME
done

REJ_DIR=$OUTPUT_DIR"rej/"
mkdir $REJ_DIR
for FILENAME in $(ls $INPUT_DIR)
do
    echo "Computing "$FILENAME" with rejection"
    timeout $TIMEOUT wmipa run $INPUT_DIR$FILENAME rejection > $REJ_DIR$FILENAME
done

# manually removing tmp directories left by processed that timed out
rm -r tmp* 2> /dev/null
