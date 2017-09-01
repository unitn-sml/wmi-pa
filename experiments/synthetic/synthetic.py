
__version__ = '0.999'
__author__ = 'Paolo Morettin'

from sys import path
path.insert(0, "../../src/")
from time import time
import matplotlib.pyplot as plt
from matplotlib.figure import figaspect

from wmiexception import WMIRuntimeException
from queryengine import QueryEngine
from wmi import WMI
from logger import Loggable

from randommodels import ModelGenerator


def error(x, y):
    """Returns the (magnitude-normalized) error between two values."""
    if x == y:
        return 0
    else:
        return abs(x - y) / min(abs(x), abs(y))

class Synthetic(Loggable):

    METHODS = [("WMI-BC", WMI.MODE_BC),
               ("WMI-ALLSMT", WMI.MODE_ALLSMT),
               ("WMI-PA", WMI.MODE_PA)]

    DEF_SEEDN = 666
    DEF_EPSILON = (10 ** -3)
    DEF_ITERATIONS = 100
    
    # default parameters for tree random formulas
    DEF_N_REALS = 2
    DEF_N_BOOLS = 4
    DEF_DEPTH = 2
    
    # default parameters for IJCAI-like random formulas
    DEF_N_CONJ = 4
    DEF_N_DISJ = 4
    
    DEF_PLOT_TEMPL = "plot_{}.png"
    MSG_EXCEPTION = "Exception occurred, iteration discarded. {}"
    MSG_NO_MATCH = "Results do not match, iteration discarded"
    MSG_RESULT = "Result: {}, elapsed time: {}"
    
    def __init__(self, epsilon=None, seedn=None):
        self.init_sublogger(__name__)
        self.epsilon = epsilon or self.DEF_EPSILON
        self.seedn = seedn or self.DEF_SEEDN

    def _matching_results(self, val1, val2):
        """Checks whether two values are identical modulo approximations.
    
        Keyword arguments:
        val1 -- first value
        val2 -- second value
    
        """
        return (error(val1, val2) <= self.epsilon)
    
    def plot(self, plot_path):
        """Plots both the computing times and the number of integrations for
        each method. Results are plotted in increasing complexity
        order according to the execution times of the first method (in
        our case, the baseline).

        Keyword arguments:
        results -- list of computing times and number of integrations
        plot_path -- path to the output file

        """
        sorted_results = sorted(self.results)
        x = range(len(sorted_results))
        plt.style.use('ggplot')
        styles = ["-.", "--", "-"]
        fontsize = 15
        linewidth = 2.5
        height_width_ratio = 0.5
        w, h = figaspect(height_width_ratio)
        fig = plt.figure(figsize = (w, h))
        
        subplot_times = fig.add_subplot(1, 2, 1)
        subplot_int = fig.add_subplot(1, 2, 2)
        method_names = map(lambda x : x[0], self.METHODS)
        for i, l in enumerate(method_names):
            y_times = map(lambda p : p[i], sorted_results)
            y_int = map(lambda p : p[i + len(method_names)], sorted_results)
            style = styles[i]
            subplot_times.plot(x, y_times, style, label = l, linewidth = linewidth)
            subplot_int.plot(x, y_int, style, label = l, linewidth = linewidth)
            
        plt.legend(loc="upper left", prop = {'size' : fontsize})
        x_label = "Formulas by increasing complexity"
        fig.text(0.5, 0.04, x_label, ha='center', va='center', fontsize = fontsize)
        subplot_times.set_ylabel("Query execution time (seconds)", fontsize = fontsize)
        subplot_int.set_ylabel("Number of integrations", fontsize = fontsize)
        
        plt.subplots_adjust(wspace = 0.3, hspace = 0.3)
        fig.savefig(plot_path, bbox_inches='tight', pad_inches=0)
        fig.show()

    @staticmethod
    def _random_query(generator, depth=1):
        """Returns a random query.

        Keyword arguments:
        generator -- A ModelGenerator instance.

        """
        return generator._random_formula(depth)
        
    def read_results(self, path):
        """Parses a results file.
        
        Keyword arguments:
        path -- path to the results file.
        
        """
        self.results = []
        with open(path, "r") as f:
            for line in f:
                try:
                    ys = map(float, line.strip().split(","))
                    self.results.append(tuple(ys))
                except ValueError:
                    continue
                


    def simulate(self, params, results_path, iterations, genmode):
        """Executes the synthetic experiment. For each combination of
        parameters, a number of iterations is performed. At each
        iteration, it randomly generates a model given the parameters
        and measures the execution times and number of integration of
        a random query.

        If the query results of the methods differ wrt a given
        tolerance or an exception is occurred, the execution times and
        number of integrations of the relative iteration are
        discarded.
        
        Results are dumped in a file during the execution.
        
        Keyword arguments:
        params -- dictionary of parameter used for generating the models
        results_path -- path to the output file
        iterations -- number of iterations for each combination of parameters
        genmode -- random generator mode (either 'ijcai' or 'tree')

        """
        self.logger.info("Running Synthetic")
        msg = "genmode: {}, seed: {}, iterations: {}, params: {}"
        self.logger.info(msg.format(genmode, self.seedn, iterations, params))
        self.results = []
        self.discarded = 0
        results_file = open(results_path, "w")

        n_reals = params['n_reals']
        n_bools = params['n_bools']
        if genmode == 'tree':
            depth = params['depth']
        elif genmode == 'ijcai':
            n_conj = params['n_conj']
            n_disj = params['n_disj']
        else:
            raise WMIRuntimeException("Invalid generation mode")
            
        gen = ModelGenerator(n_reals, n_bools, self.seedn)
        i = 0
        while i < iterations:
            msg = "iteration: {}"
            self.logger.info(msg.format(i))

            if genmode == 'tree':
                support = gen.generate_support_tree(depth)
                weights = gen.generate_weights_tree(depth)
                query = Synthetic._random_query(gen, depth)
            else:
                support = gen.generate_support_legacy(n_conj, n_disj)
                weights = gen.generate_weights_legacy()
                query = Synthetic._random_query(gen)
                

            qe = QueryEngine(support, weights)
                
            query_results = []
            execution_times = []
            n_integrations = []
            discard = False
                
            for name, mode in self.METHODS:
                self.logger.info("Computing the query with  {}".format(name))
                try:
                    start_t = time()
                    query_result, n_int = qe.perform_query(query, mode = mode)
                    exec_t = (time() - start_t)
                except WMIRuntimeException as e:
                    self.logger.warning(self.MSG_EXCEPTION.format(e))
                    discard = True
                    break

                self.logger.info(self.MSG_RESULT.format(query_result, exec_t))
                    
                for j in xrange(len(query_results) - 1):
                    previous = query_results[j]                    
                    if not self._matching_results(previous, query_result):
                        self.logger.warning(self.MSG_NO_MATCH)
                        discard = True
                        break                        

                if discard:
                    break
                
                query_results.append(query_result)
                execution_times.append(exec_t)
                n_integrations.append(n_int)                

            if not discard:
                i += 1
                result = execution_times + n_integrations
                results_file.write(",".join(map(str, result)) + "\n")
                self.results.append(result)
            else:
                self.discarded += 1

        results_file.close()
        self.logger.info("DONE! completed: {}, discarded: {}".format(
            iterations, self.discarded))

if __name__ == "__main__":        

    import argparse
    from logger import init_root_logger

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action")
    help_tree = "run the simulation with tree-shaped formulas"
    sim_tree_parser = subparsers.add_parser("simulate_tree", help=help_tree)
    
    sim_tree_parser.add_argument("-o", "--output", type=str, required=True,
                            help="output path for the results")

    sim_tree_parser.add_argument("-s", "--seed", type=int, default=None,
                            help="rng seed number")

    sim_tree_parser.add_argument("-i", "--iterations", type=int,
                            default=Synthetic.DEF_ITERATIONS,
                            help="number of iterations")

    sim_tree_parser.add_argument("-e", "--epsilon", type=float, default=None,
                            help="tolerance to rounding errors")

    sim_tree_parser.add_argument("-r", "--reals", type=int,
                default=Synthetic.DEF_N_REALS, help="number of real variables")

    sim_tree_parser.add_argument("-b", "--bools", type=int,
                default=Synthetic.DEF_N_BOOLS, help="number of Boolean variables")

    sim_tree_parser.add_argument("-d", "--depth", type=int,
                default=Synthetic.DEF_DEPTH,
                help="depth of the generated formulas (e.g. supports, queries)")

    sim_tree_parser.add_argument("-v", "--verbose", type=bool,
                            default=False,
                            help="Verbose standard output")

    sim_tree_parser.add_argument("-l", "--log", type=str,
                            default=None,
                            help="Path to the log file")

    help_ijcai = "run the simulation with ijcai-like formulas"
    sim_ijcai_parser = subparsers.add_parser("simulate_ijcai", help=help_ijcai)
    
    sim_ijcai_parser.add_argument("-o", "--output", type=str, required=True,
                            help="output path for the results")

    sim_ijcai_parser.add_argument("-s", "--seed", type=int, default=None,
                            help="rng seed number")

    sim_ijcai_parser.add_argument("-i", "--iterations", type=int,
                            default=Synthetic.DEF_ITERATIONS,
                            help="number of iterations")

    sim_ijcai_parser.add_argument("-e", "--epsilon", type=float, default=None,
                            help="tolerance to rounding errors")

    sim_ijcai_parser.add_argument("-r", "--reals", type=int,
                default=Synthetic.DEF_N_REALS, help="number of real variables")

    sim_ijcai_parser.add_argument("-b", "--bools", type=int,
                default=Synthetic.DEF_N_BOOLS, help="number of Boolean variables")

    sim_ijcai_parser.add_argument("--n-conj", type=int,
                default=Synthetic.DEF_N_CONJ,
                help="number of conjuncts")

    sim_ijcai_parser.add_argument("--n-disj", type=int,
                default=Synthetic.DEF_N_DISJ,
                help="maximum number of disjuncts")

    sim_ijcai_parser.add_argument("-v", "--verbose", type=bool,
                            default=False,
                            help="Verbose standard output")

    sim_ijcai_parser.add_argument("-l", "--log", type=str,
                            default=None,
                            help="Path to the log file")        
    
    
    plot_parser = subparsers.add_parser("plot", help="plot results")
    plot_parser.add_argument("-i", "--input", type=str, required=True,
                             help="path to the results to be plotted")

    plot_parser.add_argument("-o", "--output", type=str, default=None,
                             help="output path for the plot")

    args = parser.parse_args()
    
    if args.action == "simulate_tree":
        init_root_logger(args.log, args.verbose)
        synthetic = Synthetic(args.epsilon, args.seed)
        params = {'n_reals' : args.reals,
                   'n_bools' : args.bools,
                   'depth' : args.depth}

        synthetic.simulate(params, args.output, args.iterations, genmode='tree')

    if args.action == "simulate_ijcai":
        init_root_logger(args.log, args.verbose)
        synthetic = Synthetic(args.epsilon, args.seed)
        params = {'n_reals' : args.reals,
                   'n_bools' : args.bools,
                  'n_conj' : args.n_conj,
                  'n_disj' : args.n_disj}

        synthetic.simulate(params, args.output, args.iterations, genmode='ijcai')
        
    elif args.action == "plot":
        synthetic = Synthetic()
        synthetic.read_results(args.input)
        if args.output == None:
            args.output = synthetic.DEF_PLOT_TEMPL.format(args.input)
        synthetic.plot(args.output)
        
    else:
        assert(False), "Unrecognized action"
