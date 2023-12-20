import os

from wmibench.synthetic.synthetic_pa import generate_benchmark

N_PROBLEMS = 10
SEED = 666

MIN_BOOLS = 3
MAX_BOOLS = 3
MIN_REALS = 3
MAX_REALS = 3
MIN_DEPTH = 4
MAX_DEPTH = 7


def main():
    exp_dir = "synthetic_exp"
    data_dir = os.path.join(exp_dir, "data")
    res_dir = os.path.join(exp_dir, "results")

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(res_dir, exist_ok=True)

    for n_bools in range(MIN_BOOLS, MAX_BOOLS + 1):
        for n_reals in range(MIN_REALS, MAX_REALS + 1):
            for depth in range(MIN_DEPTH, MAX_DEPTH + 1):
                generate_benchmark(data_dir, n_reals, n_bools, depth, N_PROBLEMS, SEED)


if __name__ == "__main__":
    main()
