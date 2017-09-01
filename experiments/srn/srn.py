"""This module implements the main class for the Strategic Road Network
experiment.
"""

__version__ = '0.999'
__author__ = 'Paolo Morettin'

from time import time
from os.path import isfile
from math import sqrt
from random import choice, randint, seed
import networkx as nx
import matplotlib.pyplot as plt

from sys import path
path.insert(0, "../../src/")

from wmi import WMI
from queryengine import QueryEngine
from praise import PRAiSE
from wmiexception import WMIRuntimeException
from srnwmi import SRNWMI
from srnpraise import SRNPRAiSE
from srnparser import SRNParser
from logger import Loggable

def error(x, y):
    """Returns the (magnitude-normalized) error between two values."""    
    if x == y:
        return 0
    else:
        return abs(x - y) / min(abs(x), abs(y))

def average(values):
    assert(len(values) > 0), "Empty iterable"    
    return sum(values) / float(len(values))


class StrategicRoadNetwork(Loggable):

    PRAiSE_MODEL_PATH = "praise_srn.txt"
    PREPROCESSED_TEMPL = "{}_p{}.preprocessed"
    
    DEF_EPSILON = (10 ** -3)
    DEF_ITERATIONS = 5
    DEF_SEEDN = 666
    DEF_MIN_LENGTH = 2
    DEF_MAX_LENGTH = 6
    DEF_N_PARTITIONS = 12
    DEF_RESULTS_TEMPL = "results_np{}_s{}.csv"
    DEF_PLOT_TEMPL = "plot_{}.png"
    MSG_EXCEPTION = "Exception occurred, iteration discarded. {}"
    MSG_NO_MATCH = "Results do not match, iteration discarded"
    MSG_RESULT = "Result: {}, elapsed time: {}"

    def __init__(self, epsilon = None, seedn = None):
        self.epsilon = epsilon or self.DEF_EPSILON
        self.seedn = seedn or self.DEF_SEEDN
        self.init_sublogger(__name__)
        self.graph = None
        self.partitions = None
        seed(self.seedn)

    def simulate(self, step_list, output_path, iterations = DEF_ITERATIONS):
        """Executes the Strategic Road Network experiment. For each step length,
        a number of iterations is performed. At each iteration, it randomly
        generates a query characterized by the departure time, the path and the
        arrival time. 
        If the query results of the methods differ wrt a given tolerance or an
        exception is occurred, the execution times of the relative iteration are
        discarded.

        Results are dumped in a CSV file during the execution.

        Keyword arguments:
        step_list -- list of step lengths
        output_path -- path to the output file
        iterations -- number of iterations for each combination of parameters.

        """
        if not self.graph:
            msg = "No data to query."
            self.logger.error(msg)
            raise WMIRuntimeException(msg)

        self.logger.info("Running SRN")
        msg = "Seed: {}, steps: {}, iters: {}, n_partitions: {}, epsilon: {}"
        self.logger.info(msg.format(self.seedn, step_list, iterations,
                                    len(self.partitions)-1, self.epsilon))

        self.results = []
        self.max_error = 0
        self.discarded = 0
        f_results = open(output_path, "w")
        praise = PRAiSE()
        srn_wmi = SRNWMI(self.graph, self.partitions)
        srn_praise = SRNPRAiSE(self.graph, self.partitions)     
        for n_steps in step_list:
            wmi_times = []
            praise_times = []
            i = 0
            while i < iterations:
                self.logger.info("Steps: {}, iteration: {}".format(n_steps,
                                                                   i + 1))
                path, t_steps = self._generate_query_data(n_steps)
                t_dep = t_steps[0]
                t_arr = t_steps[-1]
                # compile the knowledge according to the path
                srn_wmi.compile_knowledge(path)
                srn_praise.compile_knowledge(path, t_dep)
                qe = QueryEngine(srn_wmi.formula, srn_wmi.weights)
                wmi_query = srn_wmi.arriving_before(t_arr)
                praise_query = [srn_praise.arriving_before(t_arr)]
                wmi_evidence = srn_wmi.departing_at(t_dep)
                self.logger.info("Computing the query with WMI-PA")
                try:
                    cti = time()
                    res1, _ = qe.perform_query(wmi_query, wmi_evidence,
                                                 mode = WMI.MODE_PA)
                    cte1 = (time() - cti)
                except WMIRuntimeException as e:
                    self.logger.warning(self.MSG_EXCEPTION.format(e))
                    self.discarded += 1
                    continue

                self.logger.info(self.MSG_RESULT.format(res1, cte1))
                praise.model = srn_praise.model
                praise.dump_model(StrategicRoadNetwork.PRAiSE_MODEL_PATH)
                self.logger.info("Computing the query with PRAiSE")
                try :
                    cti = time()
                    res2 = praise.perform_query(" and ".join(praise_query))
                    cte2 = (time() - cti)
                except Exception as e:
                    self.logger.warning(self.MSG_EXCEPTION.format(e))
                    self.discarded += 1
                    continue                    
                self.logger.info(self.MSG_RESULT.format(res2, cte2))
                
                if not self._matching_results(res1, res2):
                    self.logger.warning(self.MSG_NO_MATCH)
                    self.discarded += 1
                    continue

                i += 1
                wmi_times.append(cte1)
                praise_times.append(cte2)

            e_t_wmi = average(wmi_times)
            e_t_praise = average(praise_times)

            stdev_t_wmi = sqrt(average([(e_t_wmi - x)**2 for x in wmi_times]))
            stdev_t_praise = sqrt(average([(e_t_praise - x)**2 for x in praise_times]))            

            result = (n_steps, e_t_wmi, stdev_t_wmi,
                      e_t_praise, stdev_t_praise)
            self.results.append(result)
            f_results.write(",".join(map(str, result)) + "\n")            

        f_results.close()
        self.logger.info("Done. Discarded: {}".format(self.discarded))        
            
    def get_random_path(self, n_steps):
        if not self.graph:
            raise WMIRuntimeException("No data to query.")

        # assumption: the directed graph is strongly connected, which is true
        # pick a random starting node
        path = [choice(self.graph.nodes())]
        while len(path) != (n_steps + 1):
            # pick a random neighbor of the last node in the partial path
            current_node = path[-1]
            next_node = choice(self.graph.neighbors(current_node))
            path.append(next_node)

        return path

    def _read_preprocessed_dataset(self, path):
        '''Reads a preprocessed dataset and generates the knowledge base.

        Keyword arguments:
        path -- the path of the preprocessed dataset

        '''
        preprocessed_data = SRNParser.read_preprocessed_dataset(path)
        entries, self.partitions = preprocessed_data
        self._parse_entries(entries)

    def read_raw_dataset(self, path, n_partitions):
        '''Reads a raw dataset, performs the preprocessing and generates the
        knowledge base. Optionally, dumps the preprocessed data in a file for
        future uses.

        Keyword arguments:
        path -- path of the raw dataset to be read
        n_partitions -- number of time intervals in the day

        '''
        parser = SRNParser(n_partitions)
        pp_path = self.PREPROCESSED_TEMPL.format(path, n_partitions)
        if isfile(pp_path):
            msg = "Previously preprocessed data was found.\n" +\
                  "Remove {} and run again to preprocess the data from scratch."
            self.logger.info(msg.format(pp_path))
            self._read_preprocessed_dataset(pp_path)
        else:
            msg = "No preprocessed data was found, parsing the raw data."
            self.logger.info(msg)
            preprocessed_data = parser.read_raw_dataset(path, pp_path)
            entries, self.partitions = preprocessed_data
            self._parse_entries(entries)
            
        self.logger.info("Parsing done!")

    def _matching_results(self, val1, val2):
        """Checks whether two values are identical modulo approximations.
    
        Keyword arguments:
        val1 -- first value
        val2 -- second value        
        
        """
        delta = error(val1, val2)
        self.max_error = max(delta, self.max_error)
        return (delta <= self.epsilon)                    

    def _generate_query_data(self, n_steps):
        # pick a random path and compute the average duration
        path  = self.get_random_path(n_steps)
        t_min, t_max = self.partitions[0], self.partitions[-1]
        t_steps = [randint(0, (t_max - t_min) / 2)]
        for i in xrange(len(path) - 1):
            curr_time = t_steps[-1]
            curr_part = self._tp_to_partition(curr_time)
            curr_node, next_node = path[i], path[i + 1]
            avg_jt = self.graph[curr_node][next_node][curr_part]['avg']
            t_steps.append(curr_time + avg_jt)

        return path, t_steps        

    def _parse_entries(self, entries):
        self.graph = nx.DiGraph()
        # store the data in a graph
        # also stores the min / max journey time to further constrain the search
        self.jt_bounds = {}
        for src, dst in entries:
            self.graph.add_edge(src, dst)
            for partition in entries[(src, dst)]:
                avg, rng, coeffs = entries[(src, dst)][partition]
                self.graph[src][dst][partition] = {}
                self.graph[src][dst][partition]['avg'] = avg
                self.graph[src][dst][partition]['range'] = rng
                self.graph[src][dst][partition]['coefficients'] = coeffs
                if not (src, dst) in self.jt_bounds:
                    self.jt_bounds[(src, dst)] = list(rng)
                else:
                    if self.jt_bounds[(src, dst)][0] > rng[0]:
                        self.jt_bounds[(src, dst)][0] = rng[0]
                    if self.jt_bounds[(src, dst)][1] < rng[1]:
                        self.jt_bounds[(src, dst)][1] = rng[1]
                        
    def plot_results(self, filename):
        plt.style.use('ggplot')
        fs = 15 # font size
        ticks_fs = 15
        alpha = 0.35 # alpha value for the standard deviation
        lw = 2.5 # line width

        filter_neg = lambda l : filter(lambda x : x >= 0.0, l)
        
        sorted_results = sorted(self.results)            
        x = map(lambda p : int(p[0]), sorted_results)                
        e_pa = filter_neg(map(lambda p : p[1], sorted_results))
        stdev_pa = filter_neg(map(lambda p : p[2], sorted_results))
        e_praise = filter_neg(map(lambda p : p[3], sorted_results))
        stdev_praise = filter_neg(map(lambda p : p[4], sorted_results))

        clrs = map(lambda x : x['color'], list(plt.rcParams['axes.prop_cycle']))

        x1 = [x[index] for index in xrange(len(e_pa))]
        plt.plot(x1, e_pa, "-", label = "WMI-PA", linewidth = lw,
                 color = clrs[1])
        lower_pa = [(e_pa[i] - stdev_pa[i]) for i in xrange(len(e_pa))]
        upper_pa = [(e_pa[i] + stdev_pa[i]) for i in xrange(len(e_pa))]
        plt.fill_between(x1, lower_pa, upper_pa, alpha = alpha, linewidth = 0,
                         color = clrs[1])

        x2 = [x[index] for index in xrange(len(e_praise))]
        plt.plot(x2, e_praise, "-.", label = "PRAiSE", linewidth = lw,
                 color = clrs[2])
        lower_praise = [(e_praise[i] - stdev_praise[i])
                        for i in xrange(len(e_praise))]
        upper_praise = [(e_praise[i] + stdev_praise[i])
                        for i in xrange(len(e_praise))]
        plt.fill_between(x2, lower_praise, upper_praise, alpha = alpha,
                         linewidth = 0, color = clrs[2])

        plt.legend(loc="upper left", prop = {'size' : fs})
        plt.xlabel("Path length", fontsize = fs)
        plt.ylabel("Query execution time (seconds)", fontsize = fs)
        plt.xticks(fontsize=ticks_fs, rotation=0)
        plt.yticks(fontsize=ticks_fs, rotation=0)
        plt.subplots_adjust(wspace = 0.3, hspace = 0.3)
        plt.savefig(filename, bbox_inches='tight', pad_inches=0)
        plt.show()
        

    def _tp_to_partition(self, tp):
        for i in xrange(len(self.partitions) - 1):
            if (self.partitions[i] <= tp) and (tp < self.partitions[i + 1]):
                return i
        assert(False), "tp does not fall into any of the computed partitions."

    def read_results(self, filename):
        self.results = []
        with open(filename, "r") as f:
            for line in f:
                try:
                    ys = map(float, line.strip().split(","))
                    self.results.append(tuple(ys))
                except ValueError:
                    continue


if __name__ == "__main__":
    import argparse
    from logger import init_root_logger
    
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action")
    sim_parser = subparsers.add_parser("simulate", help="run the simulation")

    sim_parser.add_argument("-i", "--input", type=str, required=True,
                            help="path to the SRN dataset")
    
    sim_parser.add_argument("-o", "--output", type=str, default=None,
                            help="output path for the results")

    sim_parser.add_argument("-s", "--seed", type=int,
                            default=StrategicRoadNetwork.DEF_SEEDN,
                            help="rng seed number")

    sim_parser.add_argument("--iterations", type=int,
                            default=StrategicRoadNetwork.DEF_ITERATIONS,
                            help="number of iterations")

    sim_parser.add_argument("-e", "--epsilon", type=float,
                            default=StrategicRoadNetwork.DEF_EPSILON,
                            help="tolerance to rounding errors")

    sim_parser.add_argument("--min-length", type=int,
                            default=StrategicRoadNetwork.DEF_MIN_LENGTH,
                            help="minimum path length")

    sim_parser.add_argument("--max-length", type=int,
                            default=StrategicRoadNetwork.DEF_MAX_LENGTH,
                            help="maximum path length")
    
    sim_parser.add_argument("--n-partitions", type=int,
                            default=StrategicRoadNetwork.DEF_N_PARTITIONS,
                            help="number of time slots")

    sim_parser.add_argument("-v", "--verbose", type=bool,
                            default=False,
                            help="Verbose standard output")

    sim_parser.add_argument("-l", "--log", type=str,
                            default=None,
                            help="Path to the log file")    
    
    
    plot_parser = subparsers.add_parser("plot", help="plot results")
    plot_parser.add_argument("-i", "--input", type=str, required=True,
                             help="path to the results to be plotted")

    plot_parser.add_argument("-o", "--output", type=str, default=None,
                             help="output path for the plot")

    args = parser.parse_args()
    
    if args.action == "simulate":
        init_root_logger(path=args.log, verbose=args.verbose)
        if args.output == None:
            args.output = StrategicRoadNetwork.DEF_RESULTS_TEMPL.format(
                args.n_partitions, args.seed)

        srn = StrategicRoadNetwork(epsilon=args.epsilon, seedn=args.seed)
        srn.read_raw_dataset(args.input, n_partitions = args.n_partitions)

        step_list = range(args.min_length, args.max_length + 1)
        srn.simulate(step_list, args.output, args.iterations)
        
    elif args.action == "plot":
        if args.output == None:
            args.output = StrategicRoadNetwork.DEF_PLOT_TEMPL.format(args.input)
        
        srn = StrategicRoadNetwork()        
        srn.read_results(args.input)
        srn.plot_results(args.output)
        
    else:
        assert(False), "Unrecognized action"










