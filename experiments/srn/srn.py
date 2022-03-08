"""This module implements the main class for the Strategic Road Network
experiment.
"""

__version__ = '0.999'
__author__ = 'Paolo Morettin'

from time import time
from os.path import isfile
from math import sqrt
from numpy import nan
from random import choice, randint, seed
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})
from multiprocessing import Process, Queue
import psutil

import pickle

from sys import path
path.insert(0, "../../src/")

from wmipa import WMI, logger
from wmipa.wmiexception import WMIRuntimeException
from pysmt.shortcuts import *
from srnwmi import SRNWMI
from srnparser import SRNParser
from srnencodings import *

class StrategicRoadNetwork():

    SCALES = ['linear', 'log']
    
    METHOD_WMIBC = 'WMI-BC'
    METHOD_WMIALLSMT = 'WMI-ALLSMT'
    METHOD_WMIPA = 'WMI-PA'
    METHOD_WMIPA_NL = 'WMI-PA-NL'
    METHOD_WMIPA_EUF = 'WMI-PA-EUF'
    METHOD_WMIPA_EUF_TA = 'WMI-PA-EUF-TA'

    METHODS = [METHOD_WMIBC, METHOD_WMIALLSMT,
               METHOD_WMIPA, METHOD_WMIPA_NL,
               METHOD_WMIPA_EUF, METHOD_WMIPA_EUF_TA]
    CACHE = [-1, 0, 1, 2, 3]

    PREPROCESSED_TEMPL = "{}_p{}.preprocessed"

    SEPARATOR = "\n\n"
    DEF_ITERATIONS = 5
    DEF_SEEDN = 666
    DEF_MIN_LENGTH = 1
    DEF_MAX_LENGTH = 7
    DEF_N_PARTITIONS = 12    
    MSG_EXCEPTION = "Exception occurred, iteration discarded. {}"
    MSG_RESULT = "Result: {}, elapsed time: {}"

    TIMEOUT_VAL = 3600

    @staticmethod
    def DEF_LOGNAME(output):
        return "{}_log.txt".format(str(output))

    def generate(self, path, n_partitions, step_list, seedn, iterations,
                 output_path):
        """Generates a list of problems and serializes them in a Pickle file.

        Keyword arguments:
        path -- path of the raw dataset to be read
        n_partitions -- number of time intervals in the day
        step_list -- list of step lengths
        seedn -- seed number
        iterations -- number of iterations for each combination of parameters.
        output_path -- path to the output file

        """

        graph, partitions = StrategicRoadNetwork._read_raw_dataset(path, n_partitions)
        seed(seedn)
        msg = "Generating experiment\tsteps = {},\nseed = {}, iterations = {}"
        print(msg.format(step_list, seedn, iterations))

        srn_wmi = SRNWMI(graph, partitions) 
        problem_instances = []
        for n_steps in step_list:
            instances_step = []
            while len(instances_step) < iterations:
                path, t_steps = StrategicRoadNetwork._generate_query_data(graph, partitions, n_steps)
                t_dep = t_steps[0]
                t_arr = t_steps[-1]
                try:
                    srn_wmi.compile_knowledge(path)
                    wmi = WMI(srn_wmi.formula, srn_wmi.weights)
                    
                    if wmi.check_consistency(wmi.chi):
                        instance = (path, t_dep, t_arr)
                        instances_step.append(instance)
                except WMIRuntimeException:
                    continue                

            problem_instances.append((n_steps,instances_step))
        output_file = open(output_path, 'wb')
        experiment = (graph, partitions, problem_instances)
        pickle.dump(experiment, output_file)
        output_file.close()
        print("Generated {}".format(output_path))



    def simulate(self, input_path, method, cache, output_path, encoding):
        """Executes the Strategic Road Network experiment with fixed paths.

        Keyword arguments:
        input_path -- path to the experiment file
        method -- the algorithm to be tested
        output_path -- path to the output file
        encoding -- which encoding to use, see srnencodings.py
        """
        if not method in self.METHODS:
            msg = "Method not in {}".format(self.METHODS)
            raise WMIRuntimeException(msg)

        if not encoding in ENCODINGS:
            msg = "Encoding not in {}".format(ENCODINGS)
            raise WMIRuntimeException(msg)
            
        if not cache in self.CACHE:
            msg = "Cache not in {}".format(self.CACHE)
            raise WMIRuntimeException(msg)

        input_file = open(input_path, 'rb')
        graph, partitions, problem_instances = pickle.load(input_file)
        input_file.close()

        mode = {self.METHOD_WMIBC : WMI.MODE_BC,
                self.METHOD_WMIALLSMT : WMI.MODE_ALLSMT,
                self.METHOD_WMIPA : WMI.MODE_PA,
                self.METHOD_WMIPA_SA : WMI.MODE_SA_PA}

        srn_wmi = SRNWMI(graph, partitions, encoding=encoding)
        output_file = open(output_path, "wb")

        # first line is method name
        print("CACHE", cache)
        pickle.dump(method+"_"+str(cache), output_file)
        pickle.dump(StrategicRoadNetwork.SEPARATOR, output_file)

        for n_steps, instances_step in problem_instances:
            results_step = []
            print("n steps:", n_steps)
            for instance in instances_step:
                path, t_dep, t_arr = instance
                srn_wmi.compile_knowledge(path)
                wmi_query = srn_wmi.arriving_before(t_arr)
                wmi_evidence = srn_wmi.departing_at(t_dep)
                wmi = WMI(And(srn_wmi.formula, wmi_evidence), srn_wmi.weights)
                
                try:
                    cti = time()
                    q = Queue()
                    timed_proc = Process(target=StrategicRoadNetwork._get_inference, args=(wmi,
                                               mode[method],
                                               cache, 
                                               wmi_query,
                                               q))
                    timed_proc.start()
                    timed_proc.join(StrategicRoadNetwork.TIMEOUT_VAL)
                    if timed_proc.is_alive():
                        res = (None, None)
                        cte = None
                        
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
                        res = q.get()
                        cte = (time() - cti)

                except WMIRuntimeException as e:
                    print(self.MSG_EXCEPTION.format(e))
                    exit()
                    
                print(self.MSG_RESULT.format(res, cte))
                results_step.append((res, cte))
                
                # if more than half is None
                none_res = len([0 for i in results_step if i[1] is None])
                if none_res > len(instances_step)/2:
                    break

            pickle.dump((n_steps, results_step), output_file)
            pickle.dump(StrategicRoadNetwork.SEPARATOR, output_file)
            
            # if more than half is None
            none_res = len([0 for i in results_step if i[1] is None])
            if none_res > len(instances_step)/2:
                break
        
        output_file.close()
        
    @staticmethod
    def _get_inference(wmi, mode, cache, query, queue):
        res = wmi.computeWMI(Bool(True), mode=mode, cache=cache)
        res_query = wmi.computeWMI(query, mode=mode, cache=cache)
        value = res_query[0]/res[0]
        integrals = res_query[1]+res[1]
        queue.put((value, integrals))

    @staticmethod
    def _get_random_path(graph, n_steps):
        if not graph:
            raise WMIRuntimeException("No data to query.")

        # assumption: the directed graph is strongly connected, which is true
        # pick a random starting node
        path = [choice(list(graph.nodes()))]
        while len(path) != (n_steps + 1):
            # pick a random neighbor of the last node in the partial path
            current_node = path[-1]
            neigh = [n for n in graph.neighbors(current_node)]
            next_node = choice(neigh)
            path.append(next_node)

        return path

    @staticmethod
    def _read_preprocessed_dataset(path):
        preprocessed_data = SRNParser.read_preprocessed_dataset(path)
        entries, partitions = preprocessed_data
        graph = StrategicRoadNetwork._build_graph(entries)

        return graph, list(partitions)

    @staticmethod
    def _read_raw_dataset(path, n_partitions):
        pp_path = StrategicRoadNetwork.PREPROCESSED_TEMPL.format(path, n_partitions)
        if isfile(pp_path):
            msg = "Previously preprocessed data was found.\n" +\
                  "Remove {} and run again to preprocess the data from scratch."
            print(msg.format(pp_path))
            graph, partitions = StrategicRoadNetwork._read_preprocessed_dataset(pp_path)
        else:
            parser = SRNParser(n_partitions)
            preprocessed_data = parser.read_raw_dataset(path, pp_path)
            entries, partitions = preprocessed_data
            graph = StrategicRoadNetwork._build_graph(entries)

        return graph, partitions

    @staticmethod
    def _generate_query_data(graph, partitions, n_steps):
        # pick a random path and compute the average duration
        path  = StrategicRoadNetwork._get_random_path(graph, n_steps)
        t_min, t_max = partitions[0], partitions[-1]
        t_steps = [randint(0, (t_max - t_min) / 2)]
        for i in range(len(path) - 1):
            curr_time = t_steps[-1]
            curr_part = StrategicRoadNetwork._tp_to_partition(partitions, curr_time)
            curr_node, next_node = path[i], path[i + 1]
            avg_jt = graph[curr_node][next_node][curr_part]['avg']
            t_steps.append(curr_time + avg_jt)

        return path, t_steps        

    @staticmethod
    def _build_graph(entries):
        graph = nx.DiGraph()
        # store the data in a graph
        # also stores the min / max journey time to further constrain the search
        for src, dst in entries:
            graph.add_edge(src, dst)
            for partition in entries[(src, dst)]:
                avg, rng, coeffs = entries[(src, dst)][partition]
                graph[src][dst][partition] = {}
                graph[src][dst][partition]['avg'] = avg
                graph[src][dst][partition]['range'] = rng
                graph[src][dst][partition]['coefficients'] = coeffs

        return graph

    def plot_results(self, inputs, output_path, scale='linear',
                     plot_integrals=False, tables=True):
        plt.style.use('ggplot')
        #plt.axes(aspect=2.0)        
        fs = 15 # font size
        ticks_fs = 15
        alpha = 0.35 # alpha value for the standard deviation
        lw = 2.5 # line width
        clrs = list(map(lambda x : x['color'], list(plt.rcParams['axes.prop_cycle'])))
        
        plots_dict = {}
        for input_file in inputs:
            method, results = StrategicRoadNetwork._unpickle_results_file(input_file)
            if not method in plots_dict:
                plots_dict[method] = []
            plots_dict[method].extend(results)

        
        time_plots = {method : list(map(lambda x : x[0],
                              StrategicRoadNetwork.process_results(sorted(results),
                                                                   plot_integrals)))
                      for method,results in plots_dict.items()}
                      
        if plot_integrals:
            nint_plots = {method : list(map(lambda x : x[1],
                              StrategicRoadNetwork.process_results(sorted(results),
                                                                   plot_integrals)))
                      for method,results in plots_dict.items() }
                      
        # add 'timeouts' for missing values
        max_length = max(len(plot) for plot in time_plots.values())
        for plot in time_plots.values():
            if len(plot) < max_length:
                timeouts = [(i+1,) + (StrategicRoadNetwork.TIMEOUT_VAL,)*3
                            for i in range(len(plot),max_length)]
                plot.extend(timeouts)

        columns = []
        for method in self.METHODS:
            for j, cache in enumerate(self.CACHE):
                label = "{}_{}".format(method, cache)
                if not label in time_plots:
                    continue

                results = time_plots[label]
                x = list(map(lambda x : int(x[0]), results))
                mid = list(map(lambda x : x[1], results))
                low = list(map(lambda x : x[2], results))
                high = list(map(lambda x : x[3], results))

                plt.plot(x, mid, "-", label = label, linewidth = lw,
                         color = clrs[j])
                plt.fill_between(x, low, high, alpha = alpha, linewidth = 0,
                                 color = clrs[j])

                if tables:
                    col = [label] + list(map(str,list(map(int,mid))))
                    columns.append(col)
        if tables:
            first_col = ["Max. path length"] + list(map(str,range(1, max(list(map(len,columns))))))
            columns = [first_col] + columns            
            nrows = len(columns[0])
            ncols = len(columns)

            with open(output_path + "_times.txt", 'w') as f:
                header = "\\begin{tabular}{|l|" + "r|"*(ncols-1) + "}"
                f.write(header + '\n')
                f.write("\\hline\n")                
                for j in range(nrows):
                    row_elements = []
                    for i in range(len(columns)):
                        try:
                            row_elements.append(columns[i][j])
                        except IndexError:
                            row_elements.append("-")
                        row = " & ".join(row_elements) + " \\\\"

                    f.write(row + '\n')
                    f.write("\\hline\n")

                f.write("\\end{tabular}\n")

        # TIMEOUT line
        plt.plot(x, [StrategicRoadNetwork.TIMEOUT_VAL]*len(x),'--',color='r')

        leg_pos = "upper right" if scale == "linear" else "lower right"
        plt.legend(loc=leg_pos, prop = {'size' : fs})
        plt.xlabel("Maximum path length", fontsize = fs)
        plt.ylabel("Query execution time (seconds)", fontsize = fs)
        plt.xticks(fontsize=ticks_fs, rotation=0)
        plt.yticks(fontsize=ticks_fs, rotation=0)
        plt.yscale(scale)
        #plt.subplots_adjust(wspace = 0.3, hspace = 0.3)
        plt.savefig(output_path + "_times.png")#, bbox_inches='tight', pad_inches=0)
        plt.show()

        if not plot_integrals:
            return
        
        columns = []
        for method in self.METHODS:
            for j, cache in enumerate(self.CACHE):
                label = "{}_{}".format(method, cache)
                if not label in nint_plots:
                    continue

                results = nint_plots[label]
                x = list(map(lambda x : int(x[0]), results))
                mid = list(map(lambda x : x[1], results))
                low = list(map(lambda x : x[2], results))
                high = list(map(lambda x : x[3], results))
                
                to_index = len(x)
                xticks = range(x[0], x[-1]+1)
                
                # truncate where there are None
                if None in high:
                    to_index = high.index(None)
                x = x[:to_index]
                mid = mid[:to_index]
                low = low[:to_index]
                high = high[:to_index]
                
                plt.plot(x, mid, "-", label = label, linewidth = lw,
                         color = clrs[j])
                plt.fill_between(x, low, high, alpha = alpha, linewidth = 0, color = clrs[j])

                if tables:
                    col = [label] + list(map(str,list(map(int,mid))))
                    columns.append(col)

        if tables:
            first_col = ["N. steps"] + list(map(str,range(1, max(list(map(len,columns))))))
            columns = [first_col] + columns            
            nrows = len(columns[0])
            ncols = len(columns)

            with open(output_path + "_integrals.txt", 'w') as f:
                header = "\\begin{tabular}{|l|" + "r|"*(ncols-1) + "}"
                f.write(header + '\n')
                f.write("\\hline\n")                
                for j in range(nrows):
                    row_elements = []
                    for i in range(len(columns)):
                        try:
                            row_elements.append(columns[i][j])
                        except IndexError:
                            row_elements.append("-")
                        row = " & ".join(row_elements) + " \\\\"

                    f.write(row + '\n')
                    f.write("\\hline\n")

                f.write("\\end{tabular}\n")
            

        plt.legend(loc="best", prop = {'size' : fs})
        plt.xlabel("Path length", fontsize = fs)
        plt.ylabel("Number of integrations", fontsize = fs)
        plt.xticks(xticks, fontsize=ticks_fs, rotation=0)
        plt.yticks(fontsize=ticks_fs, rotation=0)
        #plt.subplots_adjust(wspace = 0.3, hspace = 0.3)
        plt.savefig(output_path + "_integrals.png")#, bbox_inches='tight', pad_inches=0)
        plt.show()                                


    @staticmethod
    def _tp_to_partition(partitions, tp):
        for i in range(len(partitions) - 1):
            if (partitions[i] <= tp) and (tp < partitions[i + 1]):
                return i
        assert(False), "tp does not fall into any of the computed partitions."

    @staticmethod
    def process_results(results, parse_integrals, median=True):
        processed = []

        for n_steps, res_step in results:
            times = [t[1] if t[1] and t[1] < StrategicRoadNetwork.TIMEOUT_VAL
                     else StrategicRoadNetwork.TIMEOUT_VAL for t in res_step]

            if median:
                q1, q2, q3 = compute_quartiles(times)
                mid = q2
                low = q1
                high = q3
            else:
                avg, stdev = compute_average_stdev(times)
                mid = avg
                low = avg - stdev
                high = avg + stdev

            noval = StrategicRoadNetwork.TIMEOUT_VAL
            low = low if low else noval
            mid = mid if mid else noval
            high = high if high else noval
            time_stats = (n_steps, mid, low, high)

            if parse_integrals:
                nint = list(map(lambda x : x[0][1], res_step))

                if median:
                    q1, q2, q3 = compute_quartiles(nint)
                    mid = q2
                    low = q1
                    high = q3
                else:
                    avg, stdev = compute_average_stdev(nint)
                    mid = avg
                    low = avg - stdev
                    high = avg + stdev

                nint_stats = (n_steps, mid, low, high)
            else:
                nint_stats = None
            
            processed.append((time_stats, nint_stats))
                    
        return processed

    @staticmethod
    def _unpickle_results_file(results_path):
        with open(results_path, 'rb') as f:
            results = []
            method = None
            text = f.read()
            separator = pickle.dumps(StrategicRoadNetwork.SEPARATOR)
            for line in text.strip().split(separator):
                if len(line) > 0:
                    try:
                        if method == None:
                            method = pickle.loads(line).strip()
                        else:
                            res = pickle.loads(line)
                            results.append(res)
                    except pickle.UnpicklingError:
                        msg = "Could not deserialize line: {}"
                        print(msg.format(line))
                    
            return method, results
            
def average(values):
    return sum(values) / float(len(values))

def median(values):
    half_vals = int(len(values)/2)
    finite_vals = [v for v in values if v is not None]
    n_finite_vals = len(finite_vals)
    if n_finite_vals > half_vals:
        # already sorted in compute_median_IQR, right? 
        # sorted_vals = sorted(finite_vals) 
        if n_finite_vals % 2 == 0:
            return (finite_vals[half_vals-1] + finite_vals[half_vals])/2
        else:
            return finite_vals[half_vals]

    return None

def compute_quartiles(values):
    assert(len(values) > 0), "Empty iterable"    
    half_vals = int(len(values)/2)

    # sort the values and put None values at the end
    sorted_vals = sorted([x for x in values if x != None])
    sorted_vals += [None] * (len(values) - len(sorted_vals))
    quart2 = median(sorted_vals)
    
    quart1 = median(sorted_vals[:half_vals])
    if len(values) % 2 == 0:
        quart3 = median(sorted_vals[half_vals:])
    else:
        quart3 = median(sorted_vals[half_vals+1:])

    return (quart1, quart2, quart3)

def compute_average_stdev(values):
    assert(len(values) > 0), "Empty iterable"
    if None in values:
        return (None, None)
    else:
        exp_val = average(values)
        stdev = sqrt(average([(exp_val - x)**2 for x in values]))
        return (exp_val, stdev)
    

if __name__ == "__main__":
    import argparse
    #from logger import init_root_logger
    
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action")

    gen_parser = subparsers.add_parser("generate", help="generate an experiment")

    gen_parser.add_argument("-i", "--input", type=str, required=True,
                            help="path to the SRN dataset")
    
    gen_parser.add_argument("-o", "--output", type=str, required=True,
                            help="output path for the experiment")

    gen_parser.add_argument("-s", "--seed", type=int,
                            default=StrategicRoadNetwork.DEF_SEEDN,
                            help="rng seed number")

    gen_parser.add_argument("--iterations", type=int,
                            default=StrategicRoadNetwork.DEF_ITERATIONS,
                            help="number of iterations")

    gen_parser.add_argument("--min-length", type=int,
                            default=StrategicRoadNetwork.DEF_MIN_LENGTH,
                            help="minimum path length")

    gen_parser.add_argument("--max-length", type=int,
                            default=StrategicRoadNetwork.DEF_MAX_LENGTH,
                            help="maximum path length")
    
    gen_parser.add_argument("--n-partitions", type=int,
                            default=StrategicRoadNetwork.DEF_N_PARTITIONS,
                            help="number of time slots")

    gen_parser.add_argument("-v", "--verbose", type=bool,
                            default=False,
                            help="Verbose standard output")

    gen_parser.add_argument("-l", "--log", type=str,
                            default=None,
                            help="Path to the log file")    

    sim_parser = subparsers.add_parser("simulate", help="run the simulation")

    sim_parser.add_argument("-i", "--input", type=str, required=True,
                            help="path to the experiment file")
    
    sim_parser.add_argument("-o", "--output", type=str, required=True,
                            help="output path for the results")

    sim_parser.add_argument("-m", "--method", choices=StrategicRoadNetwork.METHODS,
                            required=True,
                            help="Method in {}".format(StrategicRoadNetwork.METHODS))
                            
    sim_parser.add_argument("-c", "--cache", type=int, choices=StrategicRoadNetwork.CACHE,
                            required=True,
                            help="Cache in {}".format(StrategicRoadNetwork.CACHE))

    sim_parser.add_argument("-e", "--encoding", choices=ENCODINGS,
                            required=True,
                            help="Encoding in {}".format(ENCODINGS))
    
    sim_parser.add_argument("-l", "--log", type=str,
                            default=None,
                            help="Path to the log file")
    
    sim_parser.add_argument("-v", "--verbose", type=bool,
                            default=False,
                            help="Verbose standard output")    
    
    plot_parser = subparsers.add_parser("plot", help="plot results")

    plot_parser.add_argument("-i", "--inputs", nargs='+', type=str, default=None,
                             help="path to the results to be plotted")    

    plot_parser.add_argument("-o", "--output", type=str, required=True,
                             help="output path for the plot")

    plot_parser.add_argument("-l", "--log", type=str,
                            default=None,
                            help="Path to the log file")
    
    plot_parser.add_argument("-v", "--verbose", type=bool,
                            default=False,
                            help="Verbose standard output")

    plot_parser.add_argument("-s", "--scale", type=str,
                             default=StrategicRoadNetwork.SCALES[0],
                             help="one of "+str(StrategicRoadNetwork.SCALES))
    

    args = parser.parse_args()

    if args.action == "generate":
        srn = StrategicRoadNetwork()
        step_list = range(args.min_length, args.max_length + 1)
        srn.generate(args.input, args.n_partitions, step_list, args.seed,
                     args.iterations, args.output)
            
    elif args.action == "simulate":
        if args.log == None:
            args.log = StrategicRoadNetwork.DEF_LOGNAME(args.output)        
        srn = StrategicRoadNetwork()
        srn.simulate(args.input, args.method, args.cache, args.output, args.encoding)
        
    elif args.action == "plot":
        srn = StrategicRoadNetwork()
        srn.plot_results(args.inputs, args.output, args.scale,
                         plot_integrals=True)
        
    else:
        assert(False), "Unrecognized action"
