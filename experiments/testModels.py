from pysmt.shortcuts import Bool
from wmipa import WMI

if __name__ == '__main__':
    import argparse
    import sys
    import os
    import time
    import json
    from os import path
    from pysmt.shortcuts import read_smtlib
    
    parser = argparse.ArgumentParser(description='Compute WMI on models')
    parser.add_argument('input_dir', help='Name of the directory with .support and .weight files')
    parser.add_argument('output', help='Output file name on where to save all results')
    parser.add_argument('-m', '--mode', default="PA", help='Mode to use {}, default: PA'.format(WMI.MODES))
    
    args = parser.parse_args()

    input_dir = args.input_dir
    output = args.output
    mode = args.mode
    
    if mode not in WMI.MODES:
        print("Invalid mode {}, choose one: {}".format(mode, WMI.MODES))
        sys.exit(1)
    
    # check if dir exists
    if not path.exists(input_dir):
        print("Folder {} does not exists".format(input_dir))
        sys.exit(1)
        
    files = [path.join(input_dir, f) for f in os.listdir(input_dir) if path.isfile(path.join(input_dir, f))]
    support_files = [f for f in files if path.splitext(f)[1] == ".support"]
    weight_files = [f for f in files if path.splitext(f)[1] == ".weight"]
    
    n_support = len(support_files)
    n_weight = len(weight_files)
    
    if n_support <= 0:
        print("There are no supports in the folder {}".format(input_dir))
        sys.exit(1)
    if n_weight <= 0:
        print("There are no weights in the folder {}".format(input_dir))
        sys.exit(1)
        
    output_file = "{}_{}.json".format(output, mode)
    if path.exists(output_file):
        print("result.json file already exists in the folder")
        sys.exit(1)
    
    print("Found {} supports and {} weights".format(n_support, n_weight))
    
    print("Starting computing")
    time_start = time.time()
    
    results = []
    for i, s in enumerate(support_files):
        support = read_smtlib(s)
        
        for j, w in enumerate(weight_files):
            weight = read_smtlib(w)
            wmi = WMI(support, weight)
            
            time_cache = time.time()
            result_cache, n_cache = wmi.computeWMI(Bool(True), mode=mode, cache=True)
            time_cache = time.time() - time_cache
            
            time_normal = time.time()
            result_normal, n_normal = wmi.computeWMI(Bool(True), mode=mode, cache=False)
            time_normal = time.time() - time_normal
            
            res = {
                "support": s,
                "weight": w,
                "normal": {"res":result_normal, "n_integrations":n_normal, "time":time_normal},
                "cache":  {"res":result_cache, "n_integrations":n_cache, "time":time_cache}
            }
            results.append(res)
            
            print("\r"*100, end='')
            print("Support: {}/{}, Weight: {}/{}".format(i+1, n_support, j+1, n_weight), end='')
    
    print()
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)
    print("Created result.json")
    
    time_end = time.time()
    seconds = time_end - time_start
    print("Done! {:.3f}s".format(seconds))
