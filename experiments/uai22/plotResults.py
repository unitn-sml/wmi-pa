if __name__ == '__main__':
    import argparse
    import sys
    import os
    import time
    import json
    import math
    import statistics
    import matplotlib.pyplot as plt
    from os import path
    from wmipa import WMI

    parser = argparse.ArgumentParser(description='Plot WMI results')
    parser.add_argument('input', nargs='+', help='Folder and/or files containing result files as .json')
    parser.add_argument('-o', '--output', default=os.getcwd(), help='Output folder where to put the plots (default: cwd)')
    parser.add_argument('-f', '--filename', default=str(int(time.time())), help='String to add to the name of the plots (optional)')

    args = parser.parse_args()

    inputs = args.input
    output_dir = args.output
    filename = args.filename

    if not path.exists(output_dir):
        print("Folder '{}' does not exists".format(output_dir))
        sys.exit(1)

    # get all .json files
    input_files = []
    for inp in inputs:
        if not path.exists(inp):
            print("'{}' input does not exist".format(inp))
            sys.exit(1)
        if path.isfile(inp):
            name, ext = path.splitext(inp)
            if ext == ".json":
                input_files.append(inp)
            else:
                print("'{}' is not a .json file".format(inp))
                sys.exit(1)
        elif path.isdir(inp):
            inp_files = [path.join(inp, f) for f in os.listdir(inp)]
            for f in inp_files:
                if path.isfile(f):
                    name, ext = path.splitext(f)
                    if ext == ".json":
                        input_files.append(f)

    if len(input_files)<=0:
        print("No .json file found")
        sys.exit(1)

    input_files = sorted(input_files)

    print("Files found:\n\t{}".format("\n\t".join(input_files)))

    params = None
    for f in input_files:
        with open(f) as json_file:
            data = json.load(json_file)
            p = sorted(list(data["params"].keys()))
            if params is None:
                params = p
            elif p != params:
                print("Parameters to evaluate does not match in all the files (found [{}] and [{}])".format(", ".join(p), ", ".join(params)))
                sys.exit(1)

    print("Parameters to evaluate: {}".format(", ".join(params)))

    print("Started plotting")
    time_start = time.time()
    results = {}
    wmi_results = {}

    # for every input
    for f in input_files:
        with open(f) as json_file:
            data = json.load(json_file)

            p_key = tuple([data["params"][key] for key in params])
            if p_key not in results:
                results[p_key] = {}

            mode = data["mode"]
            if mode not in results[p_key]:
                # [time, int]
                results[p_key][mode] = [[], []];

            for res in data["results"]:
                results[p_key][mode][0].append(res["time"])
                if res["n_integrations"] != None:
                    results[p_key][mode][1].append(res["n_integrations"])

                files_key = (res["support"], res["weight"])
                if files_key not in wmi_results:
                    wmi_results[files_key] = {"results":[], "mode":[]}
                wmi_results[files_key]["results"].append(res["value"])
                wmi_results[files_key]["mode"].append(mode)

    # compute average value and standard deviation
    for key in results:
        for mode in results[key]:
            res = results[key][mode]
            avg_time = statistics.mean(res[0])
            avg_int = statistics.mean(res[1])
            sd_time = statistics.stdev(res[0])
            sd_int = statistics.stdev(res[1])
            results[key][mode] = [avg_time, sd_time, avg_int, sd_int]

    mode_names = []

    for index_to_evaluate in range(len(params)):
        values = {}
        for key in results:
            subkey = tuple([v for (i, v) in enumerate(key) if i != index_to_evaluate])
            if subkey not in values:
                values[subkey] = {}
            fixed_params = key[index_to_evaluate]
            values[subkey][fixed_params] = results[key]

        for fixed_params in values:
            res_group = values[fixed_params]
            x_values = sorted(list(res_group.keys()))
            if len(x_values) > 1:
                plot_axis = {}
                for x in x_values:
                    res_modes = res_group[x]
                    for mode in res_modes:
                        avg_time, sd_time, avg_integrations, sd_integrations = res_modes[mode]
                        if mode not in plot_axis:
                            plot_axis[mode] = {
                                "x":[],
                                "time_avg":[],
                                "integrations_avg":[],
                                "time_sd":[],
                                "integrations_sd":[]
                            }
                            mode_name = mode.split("_")[0]
                            if mode_name not in mode_names:
                                mode_names.append(mode_name)
                        plot_axis[mode]["x"].append(x)
                        plot_axis[mode]["time_avg"].append(avg_time)
                        plot_axis[mode]["integrations_avg"].append(avg_integrations)
                        plot_axis[mode]["time_sd"].append(sd_time)
                        plot_axis[mode]["integrations_sd"].append(sd_integrations)

                for y in ["time", "integrations"]:
                    fixed_params_name = [params[i] for i in range(len(params)) if i != index_to_evaluate]
                    assert len(fixed_params_name) == len(fixed_params)
                    fixed_params_str = ", ".join([("{}: {}".format(fixed_params_name[i], fixed_params[i])) for i in range(len(fixed_params))])
                    plt.title("{}\n{}".format(y, fixed_params_str))
                    plt.xlabel(params[index_to_evaluate])
                    plt.ylabel(y)
                    minX = maxX = None
                    for mode in plot_axis:
                        if minX is None:
                            minX = min(plot_axis[mode]["x"])
                            maxX = max(plot_axis[mode]["x"])
                        else:
                            minX = min([minX] + plot_axis[mode]["x"])
                            maxX = max([maxX] + plot_axis[mode]["x"])

                        x_axis = plot_axis[mode]["x"]
                        y_axis_avg = plot_axis[mode]["{}_avg".format(y)]
                        y_axis_sd = plot_axis[mode]["{}_sd".format(y)]
                        y_over = [y_axis_avg[i]+y_axis_sd[i] for i in range(len(y_axis_avg))]
                        y_under = [y_axis_avg[i]-y_axis_sd[i] for i in range(len(y_axis_avg))]

                        mx = min(x_axis)
                        Mx = max(x_axis)

                        plt.plot(x_axis, y_axis_avg, label=mode, marker='o')
                        plt.fill_between(range(mx, Mx+1), y_under, y_over, alpha=.1)

                    plt.xticks(range(minX, maxX+1))
                    plt.legend(fontsize='small')
                    params_values = [(str(params[i]) if i != index_to_evaluate else str(x_values[0])+"-"+str(x_values[len(x_values)-1])) for i in range(len(params))]
                    params_list = [(fixed_params_name[i][0]+str(fixed_params[i])) for i in range(len(fixed_params))] + [params[index_to_evaluate][0]+"{}-{}".format(x_values[0], x_values[len(x_values)-1])]
                    output_plot_name = "_".join(params_list)
                    output_plot_file = path.join(output_dir, "{}_{}.{}.png".format(output_plot_name, filename, y))
                    plt.savefig(output_plot_file)
                    print("Created '{}'".format(output_plot_file))
                    plt.clf()

    print("Checking values")
    for files_key in wmi_results:
        item = wmi_results[files_key]
        results = item["results"]
        if (not math.isclose(min(results), max(results), abs_tol=1e-14)):
            mode_res = [("{}: {}".format(item["results"][i], item["mode"][i])) for i in range(len(item["results"]))]
            print ("Found different output with files {}:\n{}".format(files_key, "\n".join(mode_res)))

    time_end = time.time()
    seconds = time_end - time_start
    print("Done! {:.3f}s".format(seconds))
