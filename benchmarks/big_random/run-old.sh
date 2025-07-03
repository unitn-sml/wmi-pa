
#!/bin/bash

TIMEOUT=600 # seconds

INPUT_DIR="./input/"
OUTPUT_DIR="./output/"

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

