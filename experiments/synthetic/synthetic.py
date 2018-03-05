 
__version__ = '0.999'
__author__ = 'Paolo Morettin'

from sys import path
path.insert(0, "../../src/")
from time import time
import matplotlib.pyplot as plt
from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})

import pickle

from pysmt.shortcuts import read_smtlib, write_smtlib 
from wmiexception import WMIRuntimeException, WMITimeoutException
from wmiinference import WMIInference
from praiseinference import PRAiSEInference
from xaddinference import XADDInference
from wmi import WMI
from logger import Loggable

from randommodels import ModelGenerator


class Synthetic(Loggable):

    SCALES = ['linear', 'log']

    TIMEOUT = "Timeout"
    ERROR = "Error"

    METHOD_WMIBC = "WMI-BC"
    METHOD_WMIALLSMT = "WMI-ALLSMT"
    METHOD_WMIPA = "WMI-PA"
    METHOD_PRAISE = "PRAiSE"
    METHOD_XADD = "XADD"

    METHOD_ORDER = [METHOD_XADD, METHOD_PRAISE, METHOD_WMIBC, METHOD_WMIALLSMT, METHOD_WMIPA]

    METHODS_WMI = [METHOD_WMIBC, METHOD_WMIALLSMT, METHOD_WMIPA]


    METHODS = {METHOD_WMIBC : lambda support, weights, query : \
               WMIInference(support, weights).perform_query(query, mode=WMI.MODE_BC, non_negative=False),
               METHOD_WMIALLSMT : lambda support, weights, query : \
               WMIInference(support, weights).perform_query(query, mode=WMI.MODE_ALLSMT, non_negative=False),
               METHOD_WMIPA : lambda support, weights, query : \
               WMIInference(support, weights).perform_query(query, mode=WMI.MODE_PA, non_negative=False),
               METHOD_PRAISE : lambda support, weights, query : \
                           (PRAiSEInference(support, weights).compute_normalized_probability(query), None),
               METHOD_XADD : lambda support, weights, query : \
                           (XADDInference(support, weights).compute_normalized_probability(query), None)}

    DEF_SEED = 666
    DEF_N_FORMULAS = 20

    # default parameters for tree random formulas
    DEF_N_REALS = 2
    DEF_N_BOOLS = 4
    DEF_DEPTH = 2
    
    # default parameters for IJCAI-like random formulas
    DEF_N_CONJ = 4
    DEF_N_DISJ = 4

    SEPARATOR = "\n\n"
    
    MSG_EXCEPTION = "Exception occurred, iteration discarded. {}"
    MSG_RESULT = "Result: {}, elapsed time: {}"

    TIMEOUT_VAL = 10100    

    @staticmethod
    def DEF_LOGNAME(output):
        return "{}_log.txt".format(str(output))
    def __init__(self):
        self.init_sublogger(__name__)

    @staticmethod
    def generate_cond(n_reals, n_bools, n_real_cond, n_bool_cond, n_formulas,
                       seed, output_path):
        gen = ModelGenerator(n_reals, n_bools, seed)
        problem_instances = []
        while len(problem_instances) < n_formulas:
            weights, support = gen.generate_cond_problem(n_real_cond, n_bool_cond)
            query = Synthetic._random_query(gen)
            try:                
                _ = WMIInference(support, weights, check_consistency=True)
                instance_name = output_path + "_" + str(len(problem_instances))
                support_name = instance_name + ".support"
                weights_name = instance_name + ".weights"
                query_name = instance_name + ".query"                
                write_smtlib(support, support_name)
                write_smtlib(weights, weights_name)
                write_smtlib(query, query_name)                
                instance = (support_name, weights_name, query_name)
                problem_instances.append(instance)                
            except WMIRuntimeException:
                continue

        output_file = open(output_path, 'w')
        pickle.dump(problem_instances, output_file)
        output_file.close()                
        

    @staticmethod
    def generate_ijcai(n_reals, n_bools, n_conj, n_disj, n_formulas,
                       seed, output_path):
        gen = ModelGenerator(n_reals, n_bools, seed)
        problem_instances = []
        while len(problem_instances) < n_formulas:
            support = gen.generate_support_ijcai17(n_conj, n_disj)
            weights = gen.generate_weights_ijcai17()
            query = Synthetic._random_query(gen)
            try:                
                _ = WMIInference(support, weights, check_consistency=True)
                instance_name = output_path + "_" + str(len(problem_instances))
                support_name = instance_name + ".support"
                weights_name = instance_name + ".weights"
                query_name = instance_name + ".query"                
                write_smtlib(support, support_name)
                write_smtlib(weights, weights_name)
                write_smtlib(query, query_name)                
                instance = (support_name, weights_name, query_name)
                problem_instances.append(instance)                
            except WMIRuntimeException:
                continue

        output_file = open(output_path, 'w')
        pickle.dump(problem_instances, output_file)
        output_file.close()                

    @staticmethod
    def generate_tree(n_reals, n_bools, depth, n_formulas, seed,
                      output_path):
        gen = ModelGenerator(n_reals, n_bools, seed)
        problem_instances = []
        while len(problem_instances) < n_formulas:
            support = gen.generate_support_tree(depth)
            weights = gen.generate_weights_tree(depth)
            query = Synthetic._random_query(gen, depth)
            try:
                _ = WMIInference(support, weights, check_consistency=True)
                instance_name = output_path + "_" + str(len(problem_instances))
                support_name = instance_name + ".support"
                weights_name = instance_name + ".weights"
                query_name = instance_name + ".query"                
                write_smtlib(support, support_name)
                write_smtlib(weights, weights_name)
                write_smtlib(query, query_name)                
                instance = (support_name, weights_name, query_name)
                problem_instances.append(instance)
            except WMIRuntimeException:
                continue

        output_file = open(output_path, 'w')
        pickle.dump(problem_instances, output_file)
        output_file.close()                



    def simulate(self, input_path, method, output_path):
        """Executes a synthetic experiment.

        Keyword arguments:
        input_path -- path to the experiment files
        method -- a string in Synthetic.METHODS
        output_path -- path to the output file

        """
        if not method in self.METHODS:
            msg = "Method not in {}".format(self.METHODS)
            raise WMIRuntimeException(msg)


        problem_instances = Synthetic._read_experiment(input_path)

        output_file = open(output_path, 'w')
        
        # first line is method name
        output_file.write(method + Synthetic.SEPARATOR)

        # second line is experiment name
        output_file.write(input_path + Synthetic.SEPARATOR)
        
        for support, weights, query in problem_instances:
            self.logger.info("Computing the query with  {}".format(method))
            try:
                start_t = time()
                query_result, n_int = self.METHODS[method](support, weights, query)
                exec_t = (time() - start_t)
            except WMITimeoutException as e:
                self.logger.warning(e)
                query_result = Synthetic.TIMEOUT
                exec_t = None
                n_int = None                
            except WMIRuntimeException as e:
                self.logger.warning(self.MSG_EXCEPTION.format(e))
                query_result = Synthetic.ERROR
                exec_t = None
                n_int = None

            self.logger.info(self.MSG_RESULT.format(query_result, exec_t))
            res_str = pickle.dumps((query_result, exec_t, n_int))
            output_file.write(res_str + Synthetic.SEPARATOR)
                        
        output_file.close()

    @staticmethod
    def parse_results(result_paths):
        # collect the results
        time_plots, nint_plots = {}, {}
        for input_file in result_paths:
            label, experiment, results = Synthetic._unpickle_results_file(input_file)
            time_plot = map(lambda x : x[-2], results)

            if not label in time_plots:
                time_plots[label] = {}

            # cut to timeout    
            time_plots[label][experiment] = [t if t and t < Synthetic.TIMEOUT_VAL
                                             else Synthetic.TIMEOUT_VAL for t in time_plot]

            if label in Synthetic.METHODS_WMI:
                nint_plot = map(lambda x : x[-1], results)
            
                if set(nint_plot) != set([None]):
                    if not label in nint_plots:
                        nint_plots[label] = {}

                    nint_plots[label][experiment] = nint_plot

        # merge them (and check consistency)
        all_experiments = {exp for method in time_plots
                           for exp in time_plots[method].keys()}
        for method in time_plots:
            sorted_experiments = sorted(list(time_plots[method].keys()))
            if all_experiments != set(sorted_experiments):
                msg = "missing execution time data for method {}: {}"
                assert(False),  msg.format(method,
                                           all_experiments - set(sorted_experiments))

            merged_results = [x for exp in sorted_experiments
                              for x in time_plots[method][exp]]

            time_plots[method] = merged_results

        if method in Synthetic.METHODS_WMI:
            all_experiments = {exp for method in nint_plots
                                   for exp in nint_plots[method].keys()}
            for method in nint_plots:
                sorted_experiments = sorted(list(nint_plots[method].keys()))
                if all_experiments != set(sorted_experiments):
                    msg = "missing n_integrations data for method {}: {}"
                    assert(False),  msg.format(method,
                                               all_experiments - set(sorted_experiments))


                merged_results = [x for exp in sorted_experiments
                                      for x in nint_plots[method][exp]]

                nint_plots[method] = merged_results

        return time_plots, nint_plots

    def plot_results(self, result_paths, output_path, scale='linear'):

        time_plots, nint_plots = Synthetic.parse_results(result_paths)

        if result_paths == None:
            self.logger.info("Nothing to plot")
            return

        n_instances = min(len(time_plots[m]) for m in time_plots)
        table = []
        for i in xrange(n_instances):
            instance = tuple(time_plots[m][i] for m in Synthetic.METHOD_ORDER
                             if m in time_plots)
            table.append(instance)

        sorting = map(lambda x : x[0], sorted(enumerate(table),
                                              key = lambda x : x[1]))

        plt.style.use('ggplot')
        fs = 15 # font size
        ticks_fs = 15
        alpha = 0.35 # alpha value for the standard deviation
        lw = 2.5 # line width
        clrs = map(lambda x : x['color'], list(plt.rcParams['axes.prop_cycle']))
        
        for j,m in enumerate(Synthetic.METHOD_ORDER):
            if not m in time_plots:
                continue

            sorted_results = [time_plots[m][i] for i in sorting]
            plt.plot(range(len(sorted_results)), sorted_results, "-",
                     label = m, linewidth = lw, color = clrs[j])

        # TIMEOUT line
        maxval = max(max(time_plots[m]) for m in time_plots)
        if maxval > Synthetic.TIMEOUT_VAL / 2.0:
            plt.plot(range(len(sorted_results)),
                     [Synthetic.TIMEOUT_VAL]*len(sorted_results),
                 '--',color='r')
            
        plt.legend(loc="upper left", prop = {'size' : fs})
        plt.xlabel("Random problem instances", fontsize = fs)
        plt.ylabel("Query execution time (seconds)", fontsize = fs)
        plt.xticks(fontsize=ticks_fs, rotation=0)
        plt.yticks(fontsize=ticks_fs, rotation=0)
        plt.yscale(scale)

        plt.subplots_adjust(wspace = 0.3, hspace = 0.3)
        plt.savefig(output_path + "_times.png")#, bbox_inches='tight', pad_inches=0)
        plt.show()

        for j,m in enumerate(Synthetic.METHOD_ORDER):
            if not m in nint_plots:
                continue

            sorted_results = [nint_plots[m][i] for i in sorting]
            plt.plot(range(len(sorted_results)), sorted_results, "-",
                     label = m, linewidth = lw, color = clrs[j])

        plt.legend(loc="upper left", prop = {'size' : fs})
        plt.xlabel("Random problem instances", fontsize = fs)
        plt.ylabel("Number of integrations", fontsize = fs)
        plt.xticks(fontsize=ticks_fs, rotation=0)
        plt.yticks(fontsize=ticks_fs, rotation=0)
        plt.subplots_adjust(wspace = 0.3, hspace = 0.3)
        plt.savefig(output_path + "_integrals.png")#, bbox_inches='tight', pad_inches=0)
        plt.show()

    @staticmethod
    def _read_experiment(path):
        input_file = open(path, 'r')
        problem_instances = []
        for support_name, weights_name, query_name in  pickle.load(input_file):
            support = read_smtlib(support_name)
            weights = read_smtlib(weights_name)
            query = read_smtlib(query_name)
            problem_instances.append((support, weights, query))
        
        input_file.close()
        return problem_instances
        
    @staticmethod
    def _unpickle_results_file(results_path):
        with open(results_path, 'r') as f:
            results = []
            method = None
            experiment = None
            for line in f.read().strip().split(Synthetic.SEPARATOR):
                if len(line) > 0:
                    if method == None:
                        method = line.strip()
                    elif experiment == None:
                        experiment = line.strip()
                    else:
                        try:
                            res = pickle.loads(line)
                            results.append(res)
                        except pickle.UnpicklingError:
                            msg = "Could not deserialize line: {}"
                            self.logger.warning(msg.format(line))
                    
            return method, experiment, results
        
    @staticmethod
    def _random_query(generator, depth=1):
        """Returns a random query.

        Keyword arguments:
        generator -- A ModelGenerator instance.

        """
        return generator._random_formula(depth)


if __name__ == "__main__":        

    import argparse
    from logger import init_root_logger

    parser = argparse.ArgumentParser()


    parser.add_argument("-v", "--verbose", type=bool,
                            default=False,
                            help="Verbose standard output")

    parser.add_argument("-l", "--log", type=str,
                            default=None,
                            help="Path to the log file")
    
    subparsers = parser.add_subparsers(dest="action")
    help_tree = "Generate a synthetic experiment with  tree-shaped formulas"
    gen_tree_parser = subparsers.add_parser("generate_tree", help=help_tree)
    
    gen_tree_parser.add_argument("-o", "--output", type=str, required=True,
                            help="output path for the experiment")

    gen_tree_parser.add_argument("-s", "--seed", type=int, default=None,
                            help="rng seed number")

    gen_tree_parser.add_argument("-n", "--n_formulas", type=int,
                            default=Synthetic.DEF_N_FORMULAS,
                            help="number of problem instances")

    gen_tree_parser.add_argument("-r", "--n_reals", type=int,
                default=Synthetic.DEF_N_REALS, help="number of real variables")

    gen_tree_parser.add_argument("-b", "--n_bools", type=int,
                default=Synthetic.DEF_N_BOOLS, help="number of Boolean variables")

    gen_tree_parser.add_argument("-d", "--depth", type=int,
                default=Synthetic.DEF_DEPTH,
                help="depth of the generated formulas (e.g. supports, queries)")

    help_ijcai = "Generate a synthetic experiment with ijcai17-like formulas"
    gen_ijcai_parser = subparsers.add_parser("generate_ijcai17", help=help_ijcai)
    
    gen_ijcai_parser.add_argument("-o", "--output", type=str, required=True,
                            help="output path for the experiment")

    gen_ijcai_parser.add_argument("-s", "--seed", type=int, default=None,
                            help="rng seed number")

    gen_ijcai_parser.add_argument("-n", "--n_formulas", type=int,
                            default=Synthetic.DEF_N_FORMULAS,
                            help="number of problem instances")

    gen_ijcai_parser.add_argument("-r", "--n_reals", type=int,
                default=Synthetic.DEF_N_REALS, help="number of real variables")

    gen_ijcai_parser.add_argument("-b", "--n_bools", type=int,
                default=Synthetic.DEF_N_BOOLS, help="number of Boolean variables")

    gen_ijcai_parser.add_argument("--n_conj", type=int,
                default=Synthetic.DEF_N_CONJ,
                help="number of conjuncts")

    gen_ijcai_parser.add_argument("--n_disj", type=int,
                default=Synthetic.DEF_N_DISJ,
                help="maximum number of disjuncts")

    gen_ijcai_parser.add_argument("-v", "--verbose", type=bool,
                            default=False,
                            help="verbose standard output")

    gen_ijcai_parser.add_argument("-l", "--log", type=str,
                            default=None,
                            help="path to the log file")

    help_cond = "Generate a synthetic experiment by varying the number/type of conditions"
    gen_cond_parser = subparsers.add_parser("generate_cond", help=help_cond)
    
    gen_cond_parser.add_argument("-o", "--output", type=str, required=True,
                            help="output path for the experiment")

    gen_cond_parser.add_argument("-s", "--seed", type=int, default=None,
                            help="rng seed number")

    gen_cond_parser.add_argument("-n", "--n_formulas", type=int,
                            default=Synthetic.DEF_N_FORMULAS,
                            help="number of problem instances")

    gen_cond_parser.add_argument("-r", "--n_reals", type=int,
                default=Synthetic.DEF_N_REALS, help="number of real variables")

    gen_cond_parser.add_argument("-b", "--n_bools", type=int,
                default=Synthetic.DEF_N_BOOLS, help="number of Boolean variables")

    gen_cond_parser.add_argument("--n_real_cond", type=int, required=True,
                                 help="number of LRA conditions")

    gen_cond_parser.add_argument("--n_bool_cond", type=int, required=True,
                                 help="number of Boolean conditions")

    gen_cond_parser.add_argument("-v", "--verbose", type=bool,
                            default=False,
                            help="verbose standard output")

    gen_cond_parser.add_argument("-l", "--log", type=str,
                            default=None,
                            help="path to the log file")
    
    
    sim_parser = subparsers.add_parser("simulate", help="Run experiment")
    sim_parser.add_argument("-i", "--input", type=str, required=True,
                             help="path to the experiment")

    sim_parser.add_argument("-m", "--method", type=str, required=True,
                             help="one of "+str(Synthetic.METHODS.keys()))
    
    sim_parser.add_argument("-o", "--output", type=str, required=True,
                             help="output path for the results")

    
    plot_parser = subparsers.add_parser("plot", help="plot results")
    plot_parser.add_argument("-i", "--input", nargs='+', type=str, required=True,
                             help="path to the results to be plotted")

    plot_parser.add_argument("-o", "--output", type=str, required=True,
                             help="output path for the plots")

    plot_parser.add_argument("-s", "--scale", type=str,
                             default=Synthetic.SCALES[0],
                             help="one of "+str(Synthetic.SCALES))
    

    args = parser.parse_args()
    if args.log == None:
        args.log = Synthetic.DEF_LOGNAME(args.output)

    if args.action == "generate_tree":
        init_root_logger(args.log, args.verbose)        
        Synthetic.generate_tree(args.n_reals, args.n_bools, args.depth,
                                args.n_formulas, args.seed, args.output)

    elif args.action == "generate_ijcai17":
        init_root_logger(args.log, args.verbose)
        Synthetic.generate_ijcai(args.n_reals, args.n_bools, args.n_conj,
                                 args.n_disj, args.n_formulas, args.seed,
                                 args.output)
        
    elif args.action == "generate_cond":
        init_root_logger(args.log, args.verbose)
        Synthetic.generate_ijcai(args.n_reals, args.n_bools, args.n_real_cond,
                                 args.n_bool_cond, args.n_formulas, args.seed,
                                 args.output)

    elif args.action == "simulate":
        init_root_logger(args.log, args.verbose)
        synthetic = Synthetic()
        synthetic.simulate(args.input, args.method, args.output)
        
    elif args.action == "plot":
        synthetic = Synthetic()
        synthetic.plot_results(args.input, args.output, args.scale)
        
    else:
        assert(False), "Unrecognized action"
