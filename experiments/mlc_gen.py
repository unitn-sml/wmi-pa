#!/usr/bin/env python3

import os

from wmibench.uci_det.uci_det import generate_benchmark

N_MIN = 100
N_MAX = 200
N_QUERIES = 5
SEED = 666
QHs = [0.0, 0.25, 0.5, 0.75, 1.0]


def main():
    exp_dir = "mlc"
    data_dir = os.path.join(exp_dir, "data")
    res_dir = os.path.join(exp_dir, "results")

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(res_dir, exist_ok=True)

    for qh in QHs:
        qh_str = f'uci-det-m:{N_MIN}-M:{N_MAX}-N:{N_QUERIES}-Q:{qh}-S:{SEED}'
        qh_dir = os.path.join(data_dir, qh_str)
        generate_benchmark(N_MIN, N_MAX, N_QUERIES, qh, qh_dir, SEED)


if __name__ == "__main__":
    main()
