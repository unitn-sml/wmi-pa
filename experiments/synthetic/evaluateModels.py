import psutil
from pysmt.shortcuts import Bool, BOOL, REAL, get_free_variables
from wmipa import WMI
from multiprocessing import Process, Queue
from pywmi import Domain
from pywmi.engines import PyXaddEngine, XsddEngine


def get_real_bounds(support):
    domain, _ = support.args()
    bounds = {}
    for bound in domain.args():
        lb, ub = bound.args()
        lb, var1 = lb.args()
        var2, ub = ub.args()
        assert var1 == var2
        var_name = var1.symbol_name()
        bounds[var_name] = (lb.constant_value(), ub.constant_value())
    return bounds

def compute_wmi(wmi, domain, mode, cache, q):
    if "PA" in mode:
        res = wmi.computeWMI(Bool(True), mode=mode, cache=cache, 
            domA=set(domain.get_bool_symbols()),
            domX=set(domain.get_real_symbols()))
        res = (*res, wmi.integrator.get_integration_time())
    else:
        res = (wmi.compute_volume(), 0, 0)
    # it = wmi.integrator.get_integration_time()
    q.put(res)

if __name__ == '__main__':
    import argparse
    import sys
    import os
    import time
    import json
    import re
    from os import path
    from pysmt.shortcuts import read_smtlib
    
    modes = ["{}_cache_{}".format(m, i) for m in WMI.MODES for i in range(0, 4)] + WMI.MODES + ["XADD", "XSDD"]
    
    parser = argparse.ArgumentParser(description='Compute WMI on models')
    parser.add_argument('input', help='Folder with .support and .weight files')
    parser.add_argument('-o', '--output', default=os.getcwd(), help='Output folder where to save the result (default: cwd)')
    parser.add_argument('-f', '--filename', help='Name of the result file (optional)')
    parser.add_argument('-m', '--mode', choices=modes, required=True, help='Mode to use')
    parser.add_argument('--threads', default=None, type=int, help='Number of threads to use for WMIPA')
    parser.add_argument('-e', '--equals', action='store_true', help='Set this flag if you want to compute wmi only on support and weight with same name')
    parser.add_argument('-t', '--stub', action="store_true", help='Set this flag if you only want to count the number of integrals to be computed')
    parser.add_argument('--timeout', type=int, default=3600, help='Max time (in seconds)')
    
    args = parser.parse_args()

    input_dir = args.input
    output_dir = args.output
    output_file = args.filename
    mode = args.mode
    equals = args.equals
    timeout = args.timeout
    threads = args.threads
    
    # check if input dir exists
    if not path.exists(input_dir):
        print("Folder '{}' does not exists".format(input_dir))
        sys.exit(1)
        
    # check if output dir exists
    if not path.exists(output_dir):
        print("Folder '{}' does not exists".format(output_dir))
        sys.exit(1)
        
    if output_file is not None:
        output_file = path.join(output_dir, output_file)
        if path.exists(output_file):
            print("File '{}' already exists".format(output_file))
        
    elements = [path.join(input_dir, f) for f in os.listdir(input_dir)]
    files = [e for e in elements if path.isfile(e)]
    support_files = sorted([f for f in files if path.splitext(f)[1] == ".support"])
    weight_files = sorted([f for f in files if path.splitext(f)[1] == ".weight"])
    info_file = path.join(input_dir, "info.json")
    
    n_support = len(support_files)
    n_weight = len(weight_files)
    
    if n_support <= 0:
        print("There are no .support files in the input folder")
        sys.exit(1)
    if n_weight <= 0:
        print("There are no .weight files in the input folder")
        sys.exit(1)
    if not path.exists(info_file):
        print("There is no info.json in the input folder")
        
    print("Found {} supports and {} weights".format(n_support, n_weight))
        
    with open(info_file, 'r') as f:
        info = json.load(f)
        reals = info["real_variables"]
        bools = info["bool_variables"]
        depth = info["depth"]
    
    print("Checking variables")
    for f in support_files + weight_files:
        formula = read_smtlib(f)
        variables = get_free_variables(formula)
        for v in variables:
            v_type = v.symbol_type()
            v_name = v.symbol_name()
            type(v_type)
            if (v_type == BOOL and v_name not in bools) or (v_type == REAL and v_name not in reals):
                print("Variable '{}' in file '{}' is not present in info.json")
    
    if output_file is None:
        output_name = "r{}_b{}_d{}_{}_{}.json".format(len(reals), len(bools), depth, mode, int(time.time()))
        output_file = path.join(output_dir, output_name)
    
    print("Started computing")
    time_start = time.time()
    
    results = []

    for i, s in enumerate(support_files):
        support = read_smtlib(s)
        bounds = get_real_bounds(support)
        domain = Domain.make(bools, list(bounds.keys()), list(bounds.values()))
        assert (set(bounds.keys()) == set(reals))

        for j, w in enumerate(weight_files):
            support_filename = path.splitext(s)[0]
            weight_filename = path.splitext(w)[0]
            if not equals or support_filename == weight_filename:
                
                weight = read_smtlib(w)
                if "PA" in mode:
                    wmi = WMI(support, weight, stub_integrate=args.stub, n_threads=threads)
                else:
                    if mode == "XADD":
                        wmi = PyXaddEngine(support=support, weight=weight, domain=domain)
                    elif mode == "XSDD":
                        wmi = XsddEngine(support=support, weight=weight, domain=domain)
                
                cache = -1
                if "cache" in mode:
                    cache = int(mode.split("_")[2])
                
                time_init = time.time()
                q = Queue()
                timed_proc = Process(
                    target=compute_wmi, args = (wmi,
                                                domain,
                                                mode.split("_")[0], 
                                                cache, 
                                                q)
                )
                timed_proc.start()
                timed_proc.join(timeout)
                if timed_proc.is_alive():
                    res = (None, None, timeout)
                    time_total = timeout
                    
                    # kill the process and its children
                    pid = timed_proc.pid
                    proc = psutil.Process(pid)
                    for subproc in proc.children(recursive=True):
                        try:
                            subproc.kill()
                        except psutil.NoSuchProcess:
                            continue
                    try:
                        proc.kill()
                    except psutil.NoSuchProcess:
                        pass
                else:
                    value, n_integrations, integration_time = q.get()
                    time_total = time.time() - time_init

                res = {
                    "support": s,
                    "weight": w,
                    "value":value,
                    "n_integrations":n_integrations,
                    "time":time_total,
                    "integration_time":integration_time
                }
                results.append(res)
                
                print("\r"*100, end='')
                print("Support: {}/{}, Weight: {}/{}".format(i+1, n_support, j+1, n_weight), end='')
    
    print()
    print("Computed {} WMI".format(len(results)))
    if len(results) == 0:
        sys.exit(1)
    
    info = {
        "params":{
            "real": len(reals),
            "bool": len(bools),
            "depth": depth
        },
        "mode": mode,
        "results": results
    }
    with open(output_file, 'w') as f:
        json.dump(info, f, indent=4)
    print("Created {}".format(output_file))
    
    seconds = time.time() - time_start
    print("Done! {:.3f}s".format(seconds))
