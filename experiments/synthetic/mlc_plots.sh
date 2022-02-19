MLC_DIR=mlc

mkdir -p $MLC_DIR/plots

for dataset in $(ls $MLC_DIR/results | grep dets-100)
do
    python3 plotUAI.py $MLC_DIR/results/$dataset -o $MLC_DIR/plots/ -f _${dataset}_cactus --cactus
done
