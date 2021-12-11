from wmipa import WMI

def run (cmd):
    output = subprocess.run(cmd, stderr=subprocess.PIPE)
    if output.returncode == 1:
        print("\n\nError with command {}:\n".format(" ".join(cmd)))
        err = output.stderr.decode("utf-8")
        for line in err.split('\n'):
            print(line)
        sys.exit(1)

def get_range(value):
    if "-" in value:
        interval = value.split("-")
        values = [i for i in range(int(interval[0]), int(interval[1])+1)]
    else:
        values = [(int(value))]
    return values

if __name__ == '__main__':
    import argparse
    import sys
    import os
    import time
    import subprocess
    from os import path
    
    default_modes = ["{}_cache_{}".format(m, i) for m in WMI.MODES for i in range(0, 4)] + WMI.MODES
    
    parser = argparse.ArgumentParser(description='Plot WMI results')
    parser.add_argument('output', help='Name of new folder where all files will be put')
    parser.add_argument('-r', '--reals', required=True, help='Number of real variables')
    parser.add_argument('-b', '--booleans', required=True, help='Number of bool variables')
    parser.add_argument('-d', '--depth', required=True, help='Depth of the formula tree')
    parser.add_argument('-m', '--models', required=True, help='Number of models per dataset')
    parser.add_argument('-e', '--equals', action='store_true', help='Set this flag if you want to compute wmi only on support and weight with same name')
    parser.add_argument('-s', '--seed', default=None, help='Random seed')
    parser.add_argument('-t', '--stub', action="store_true", help='Set this flag if you only want to count the number of integrals to be computed')
    parser.add_argument('--modes', nargs='*', choices=default_modes, help='List of all modes (optional)')
    
    args = parser.parse_args()

    output_dir = args.output
    reals = args.reals
    bools = args.booleans
    depth = args.depth
    models = args.models
    equals = args.equals
    modes = args.modes
    seed = args.seed
    stub = args.stub
    
    if equals:
        equals = ["-e"]
    else:
        equals = []
    if stub:
        stub = ["-t"]
    else:
        stub = []
    
    if modes is None:
        modes = default_modes
    elif len(modes) != len(set(modes)):
        print("Duplicate mode")
        sys.exit(1)
    
    if path.exists(output_dir):
        print("'{}' folder already exists".format(output_dir))
        sys.exit(1)
    else:
        os.mkdir(output_dir)
    
    reals = get_range(reals)
    bools = get_range(bools)
    depth = get_range(depth)
    if seed is not None:
        seeds = get_range(seed)
    
    if len(reals+bools+depth) == 3:
        print("No parameter with range specified")
        sys.exit(1)

    data_dir = path.join(output_dir, "data")
    results_dir = path.join(output_dir, "results")
    plots_dir = path.join(output_dir, "plots")
    os.mkdir(data_dir)
    os.mkdir(results_dir)
    os.mkdir(plots_dir)
    
    time_start = time.time()
    
    print("### Creating all models ###")
    # create models
    if seed is not None:
        if len(seeds) == 1:
            seeds = (seeds[0] for _ in range(len(reals) * len(bools) * len(depth)))
        seed_it = iter(seeds)
    for r in reals:
        for b in bools:
            for d in depth:
                seed_par = [] if seed is None else ['-s', str(next(seed_it))]
                run(["python3", "randomModels.py", "-o", data_dir,
                    "-r", str(r), "-b", str(b), "-d", str(d), "-m", str(models)] + 
                    seed_par)
                    
    # test models
    for mode in modes:
        print("### Computing WMI with mode {} ###".format(mode))
        datasets = os.listdir(data_dir)
        for i, f in enumerate(datasets):
            f = path.join(data_dir, f)
            output = run(["python3", "evaluateModels.py", f, "-o", results_dir, "-m", mode] + equals + stub)
            
    # create plots
    print("### Plotting everything ###")
    output = run(["python3", "plotResults.py", results_dir, "-o", plots_dir])
    
    time_end = time.time()
    seconds = time_end - time_start
    print("### End experiment! {:.3f}s ###".format(seconds))
    
