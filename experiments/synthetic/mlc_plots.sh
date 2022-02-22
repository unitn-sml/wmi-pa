MLC_DIR=mlc

mkdir -p $MLC_DIR/plots

for qh in 0.0 0.5 1.0
do
    python3 plotUAI.py $MLC_DIR/results/*$qh* -o $MLC_DIR/plots/ -f _${qh}_cactus --cactus --timeout 1200
done
