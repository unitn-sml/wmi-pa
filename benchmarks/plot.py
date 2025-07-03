
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import os

plt.style.use("ggplot")

FIELDS = ["Z", "time", "npolys"]

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


def get_class_from_filename(filename, prefix):
    if prefix is None:
        return ""
    for farg in filename.partition(".")[0].split("-"):
        if farg.startswith(prefix):
            return farg.replace(prefix, "")

    return ""


def error_plots(exact_results, approx_results, args):

    ALPHA = 0.8
    fig = plt.figure()
    ax = fig.add_subplot()
    #ax.set_title("Approximation error")
    ax.set_xlabel(args.xlabel or "")
    if args.ylabel is not None:
        ylabel = args.ylabel
    elif args.absolute:
        ylabel = "Absolute error"
    else:
        ylabel = "Relative error"
    ax.set_ylabel(ylabel)

    sorted_f = []
    ground_truth = {}
    classes = set()
    for f in sorted(list(exact_results.keys())):
        ygt = exact_results[f].get("Z")
        if ygt is not None:
            fcl = get_class_from_filename(f, args.classes)
            ground_truth[f] = (ygt, fcl)
            sorted_f.append(f)
            classes.add(fcl)

    classes = sorted(list(classes))
    for m in args.methods:
        error = {fcl : [] for fcl in classes}
        for f in ground_truth:
            if f in approx_results[m]:
                ym = approx_results[m][f].get("Z")
                if ym is not None:
                    ygt, fcl = ground_truth[f]
                    y = abs(ygt - ym)
                    if not args.absolute:
                        y = y/ygt
                    error[fcl].append(y)

        if len(classes) == 1:
            y = error[""]
            ax.plot(range(len(y)), y, alpha=ALPHA, label=m)
        else:
            y = np.array([np.mean(error[cl]) for cl in classes])
            ystd = np.array([np.std(error[cl]) for cl in classes])
            x = list(map(int, classes))
            ax.plot(x, y, alpha=ALPHA, label=m)
            ax.fill_between(x, np.max([np.zeros(len(y)), y-ystd], axis=0), y+ystd, alpha=ALPHA / 2)

    ax.legend()
    path = os.path.join(args.output_directory, f"error.pdf")
    fig.savefig(path, bbox_inches='tight', pad_inches=0)
    if args.interactive:
        plt.show()

def runtime_scatter(xresults, yresults, args):

    MARKER = "x"
    ALPHA = 0.9
    TIMEOUT_COLOR = "red"
    DIAGONAL_COLOR = "grey"

    def get_result(res_dict, fname):
        if fname in res_dict:
            return res_dict[fname].get("time") or args.timeout
    
    all_filenames = set(xresults.keys()).union(set(yresults.keys()))
    
    xtime, ytime = {}, {}
    tmin, tmax = None, None
    for f in all_filenames:

        fcl = get_class_from_filename(f, args.classes)

        if fcl not in xtime: xtime[fcl] = []
        if fcl not in ytime: ytime[fcl] = []
        
        r1 = get_result(xresults, f)
        r2 = get_result(yresults, f)        
        xtime[fcl].append(r1)
        ytime[fcl].append(r2)

        if r1 is not None and (tmin is None or r1 < tmin): tmin = r1
        if r2 is not None and (tmin is None or r2 < tmin): tmin = r2
        if r1 is not None and (tmax is None or r1 > tmax): tmax = r1
        if r2 is not None and (tmax is None or r2 > tmax): tmax = r2

    fig = plt.figure()
    ax = fig.add_subplot()
    ax.set_title("Runtime (seconds)")
    xlabel = args.xlabel or "Method1"
    ylabel = args.ylabel or "Method2"
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    tenpercent = (tmax - tmin) * 0.1
    ax.set_xlim([tmin, tmax + tenpercent])
    ax.set_ylim([tmin, tmax + tenpercent])

    ax.set_aspect("equal")
    if args.logscale:
        ax.set_xscale("log")
        ax.set_yscale("log")

    # timeout lines
    ax.axhline(args.timeout, 0, args.timeout, linestyle="--", color=TIMEOUT_COLOR) # timeout lines and label
    ax.axvline(args.timeout, 0, args.timeout, linestyle="--", color=TIMEOUT_COLOR)
    ax.annotate("timeout", (0.02, 0.925), xycoords='axes fraction', color=TIMEOUT_COLOR)

    # diagonal line
    ax.plot([tmin, tmax+tenpercent], [tmin, tmax + tenpercent], linestyle="--", color=DIAGONAL_COLOR)

    sorted_classes = sorted(list(xtime.keys()))
    #colors = cm.viridis(np.linspace(0, 1, len(sorted_classes)))
    colors = cm.rainbow(np.linspace(0, 1, len(sorted_classes)))
    for i, cl in enumerate(sorted_classes):
        ax.scatter(xtime[cl], ytime[cl], marker=MARKER, alpha=ALPHA, color=colors[i], label=cl)

    if len(sorted_classes) > 1:
        ax.legend()
    
    path = os.path.join(args.output_directory, f"runtime-{xlabel}-vs-{ylabel}.pdf")
    fig.savefig(path, bbox_inches='tight', pad_inches=0)
    if args.interactive:
        plt.show()



if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_directory", type=str, help="Plot directory", default=".")
    parser.add_argument("--logscale", action="store_true", default=False, help="Use logscale")
    parser.add_argument("--interactive", action="store_true", default=False, help="Use logscale")
    parser.add_argument("--xlabel", type=str, help="Override xlabel")
    parser.add_argument("--ylabel", type=str, help="Override ylabel")
    
    subparsers = parser.add_subparsers(dest="plot")

    ts_parser = subparsers.add_parser("runtime-scatter")
    ts_parser.add_argument("--xpaths", type=str, nargs="+", default=[], help="Paths to Method 1's results")
    ts_parser.add_argument("--ypaths", type=str, nargs="+", default=[], help="Paths to Method 2's results")
    ts_parser.add_argument("--timeout", type=int, help="Timeout")
    ts_parser.add_argument("--classes", type=str, help="Partition classes by filename substring")

    err_parser = subparsers.add_parser("error")
    err_parser.add_argument("exact", type=str, help="Directory with exact results")
    err_parser.add_argument("--approx", type=str, nargs="+", default=[], help="Directories with approximate results")
    err_parser.add_argument("--methods", type=str, nargs="+", default=[], help="Approx. methods' names")
    err_parser.add_argument("--classes", type=str, help="Partition classes by filename substring")
    err_parser.add_argument("--absolute", action="store_true", default=False, help="Partition classes by filename substring")

    args = parser.parse_args()

    if args.plot == "runtime-scatter":
        xresults = parse_results(args.xpaths)
        yresults = parse_results(args.ypaths)
        runtime_scatter(xresults, yresults, args)

    if args.plot == "error":
        exact_results = parse_results(map(lambda f : os.path.join(args.exact, f), os.listdir(args.exact)))

        if len(args.methods) != len(args.approx):
            args.methods = [f"Method {i}" for i in range(len(args.approx))]

        approx_results = {}
        for i, m in enumerate(args.methods):
            approx_results[m] = parse_results(map(lambda f : os.path.join(args.approx[i], f), os.listdir(args.approx[i])))
        
        error_plots(exact_results, approx_results, args)
