

import matplotlib.pyplot as plt
import numpy as np
import os

FIELDS = ["Z", "time"]

def parse_results(paths):
    results = {}
    for path in paths:
        if not os.path.isfile(path):
            continue
        with open(path, "r") as f:
            filename = os.path.basename(path)
            results[filename] = dict()
            for line in f.readlines():
                for field in FIELDS:
                    if line.startswith(f"{field}: "):
                        results[filename][field] = float(line.replace(f"{field}: ", ""))

    return results
                    

def scatterplots(xresults, yresults, args):

    def get_result(res_dict, fname, field, noval):
        if fname in res_dict:
            return res_dict[fname].get(field, noval)
        else:
            return noval
            
    
    sorted_filenames = sorted(list(set(xresults.keys()).union(set(yresults.keys()))))
    print(f"N.points: {len(sorted_filenames)}")
    for field in FIELDS:
        x1, x2 = [], []
        xmin, xmax = None, None
        for f in sorted_filenames:
            noval = args.timeout if field == "time" else None
            r1 = get_result(xresults, f, field, noval)
            r2 = get_result(yresults, f, field, noval)            
            x1.append(r1)
            x2.append(r2)

            if r1 is not None and (xmin is None or r1 < xmin):
                xmin = r1
            if r2 is not None and (xmin is None or r2 < xmin):
                xmin = r2
            if r1 is not None and (xmax is None or r1 > xmax):
                xmax = r1
            if r2 is not None and (xmax is None or r2 > xmax):
                xmax = r2

        plt.style.use("ggplot")
        fig = plt.figure()
        ax = fig.add_subplot()
        ax.set_title(field)
        ax.set_xlabel(args.xlabel or "method 1")
        ax.set_ylabel(args.ylabel or "method 2")
        ax.set_xlim([xmin, xmax])
        ax.set_ylim([xmin, xmax])

        if args.logscale and field == "time":
            ax.set_xscale("log")
            ax.set_yscale("log")
        
    
        ax.scatter(x1, x2, marker='x', alpha=0.8)
        path = os.path.join(args.output_directory, f"scatter-{field}.pdf")
        fig.savefig(path, bbox_inches='tight', pad_inches=0)
        if args.interactive:
            plt.show()

        ax.cla()


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("--xpaths", type=str, nargs='+', default=[], help="Paths to Method 1's results")
    parser.add_argument("--ypaths", type=str, nargs='+', default=[], help="Paths to Method 2's results")
    parser.add_argument("--timeout", type=int, help="Timeout")
    parser.add_argument("--xlabel", type=str, help="Method 1's name")
    parser.add_argument("--ylabel", type=str, help="Method 2's name")
    parser.add_argument("--output_directory", type=str, help="Plot directory", default=".")
    parser.add_argument("--logscale", action="store_true", default=False, help="Use logscale")
    parser.add_argument("--interactive", action="store_true", default=False, help="Use logscale")

    args = parser.parse_args()
    xresults = parse_results(args.xpaths)
    yresults = parse_results(args.ypaths)
    scatterplots(xresults, yresults, args)
