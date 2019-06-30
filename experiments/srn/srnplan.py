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
import pickle
from pysmt.shortcuts import *
from multiprocessing import Process, Queue
import psutil

from sys import path
path.insert(0, "../../src/")

from wmipa import WMI
from wmipa.wmiexception import WMIRuntimeException
from srn import StrategicRoadNetwork
from planwmi import PlanWMI
from srnparser import SRNParser
from srnencodings import *


class SRNPlan(StrategicRoadNetwork):    

    PLAN_TEMPL = "{}_p{}.plan"

    def generate(self, path, n_partitions, step_list, seedn, iterations, output_path):
        """Generates a list of problems and serializes them in a Pickle file.

        Keyword arguments:
        path -- path of the raw dataset to be read
        n_partitions -- number of time intervals in the day
        step_list -- list of step lengths
        seedn -- seed number
        iterations -- number of iterations for each combination of parameters.
        output_path -- path to the output file

        """
        graph, partitions, plan = SRNPlan._read_raw_dataset(path, n_partitions)
        seed(seedn)
        msg = "Generating experiment\tsteps = {},\nseed = {}, iterations = {}"
        print(msg.format(step_list, seedn, iterations))
        
        srn_wmi = PlanWMI(partitions, plan)
        problem_instances = []
        for n_steps in step_list:
            instances_step = []
            while len(instances_step) < iterations:
                subgraph, path, t_steps = SRNPlan._generate_query_data(graph,
                                                            partitions, n_steps)
                t_dep = t_steps[0]
                t_arr = t_steps[-1]
                l_dep = path[0]
                l_arr = path[-1]
                try:
                    srn_wmi.compile_knowledge(subgraph, n_steps, l_dep, l_arr)
                    evidence = srn_wmi.departing_at(t_dep)
                    wmi = WMI(And(srn_wmi.formula, evidence), srn_wmi.weights)
                    if wmi.check_consistency(wmi.chi):
                        instance = (subgraph, l_dep, l_arr, t_dep, t_arr)
                        instances_step.append(instance)
                except WMIRuntimeException:
                    continue                

            problem_instances.append((n_steps,instances_step))


        output_file = open(output_path, 'wb')
        experiment = (partitions, plan, problem_instances)
        pickle.dump(experiment, output_file)
        output_file.close()


    def simulate(self, input_path, method, cache, output_path, encoding):
        """Executes the Strategic Road Network experiment with a conditional
        plan.

        Keyword arguments:
        input_path -- path to the experiment file
        method -- either 'wmi' or 'praise'
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
        partitions, plan, problem_instances = pickle.load(input_file)
        input_file.close()

        mode = {self.METHOD_WMIBC : WMI.MODE_BC,
                self.METHOD_WMIALLSMT : WMI.MODE_ALLSMT,
                self.METHOD_WMIPA : WMI.MODE_PA}        

        srn_wmi = PlanWMI(partitions, plan, encoding=encoding)

        output_file = open(output_path, 'wb')

        # first line is method name
        print("CACHE", cache)
        pickle.dump(method+"_"+str(cache), output_file)
        pickle.dump(StrategicRoadNetwork.SEPARATOR, output_file)

        for n_steps, instances_step in problem_instances:
            results_step = []
            for instance in instances_step:
                subgraph, l_dep, l_arr, t_dep, t_arr = instance
                srn_wmi.compile_knowledge(subgraph, n_steps, l_dep, l_arr)
                
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
    def _read_raw_dataset(path, n_partitions):
        pp_path = SRNPlan.PREPROCESSED_TEMPL.format(path, n_partitions)
        parser = SRNParser(n_partitions)
        if isfile(pp_path):
            graph, partitions = SRNPlan._read_preprocessed_dataset(pp_path)
        else:
            preprocessed_data = parser.read_raw_dataset(path, pp_path)
            entries, partitions = preprocessed_data
            graph = SRNPlan._build_graph(entries)

        plan_path = SRNPlan.PLAN_TEMPL.format(path, n_partitions)
        if isfile(plan_path):
            plan = SRNParser.read_conditional_plan(plan_path)
        else:
            plan = parser.compute_conditional_plan(graph)
            SRNParser.write_conditional_plan(plan_path, plan)
                        
        return graph, partitions, plan

    @staticmethod
    def _generate_query_data(graph, partitions, n_steps):

        reachables_n_steps = []
        while reachables_n_steps == []:
            src = choice(list(graph.nodes()))
            frontier = lambda n_steps : n_steps + 5
            reachables = nx.single_source_shortest_path_length(graph,
                        source=src, cutoff=frontier(n_steps))
            reachables_n_steps = [n for n in reachables
                                  if reachables[n] == n_steps]
            
        dst = choice(reachables_n_steps)
        
        subgraph = nx.DiGraph()
        subgraph.add_nodes_from((n, graph.nodes[n]) for n in reachables)
        subgraph.add_edges_from((n, nbr, d)
            for n, nbrs in graph.adj.items() if n in reachables
            for nbr, d in nbrs.items() if nbr in reachables)
        subgraph.graph.update(graph.graph)

        path = nx.shortest_path(subgraph, src, dst)
        
        t_min, t_max = partitions[0], partitions[-1]
        t_steps = [randint(0, (t_max - t_min) / 2)]
        for i in range(len(path) - 1):
            curr_time = t_steps[-1]
            curr_part = SRNPlan._tp_to_partition(partitions, curr_time)
            curr_node, next_node = path[i], path[i + 1]
            avg_jt = graph[curr_node][next_node][curr_part]['avg']
            t_steps.append(curr_time + avg_jt)

        return subgraph, path, t_steps


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action")
    gen_parser = subparsers.add_parser("generate", help="generate an experiment")

    gen_parser.add_argument("-i", "--input", type=str, required=True,
                            help="path to the SRN dataset")
    
    gen_parser.add_argument("-o", "--output", type=str, required=True,
                            help="output path for the experiment")

    gen_parser.add_argument("-s", "--seed", type=int,
                            default=SRNPlan.DEF_SEEDN,
                            help="rng seed number")

    gen_parser.add_argument("--iterations", type=int,
                            default=SRNPlan.DEF_ITERATIONS,
                            help="number of iterations")

    gen_parser.add_argument("--min-length", type=int,
                            default=SRNPlan.DEF_MIN_LENGTH,
                            help="minimum path length")

    gen_parser.add_argument("--max-length", type=int,
                            default=SRNPlan.DEF_MAX_LENGTH,
                            help="maximum path length")
    
    gen_parser.add_argument("--n-partitions", type=int,
                            default=SRNPlan.DEF_N_PARTITIONS,
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

    sim_parser.add_argument("-m", "--method", choices=SRNPlan.METHODS,
                            required=True,
                            help="Method in {}".format(SRNPlan.METHODS))
                            
    sim_parser.add_argument("-c", "--cache", type=int, choices=SRNPlan.CACHE,
                            required=True,
                            help="Cache in {}".format(SRNPlan.CACHE))

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


    args = parser.parse_args()

    if args.action == "generate":
        srn = SRNPlan()
        step_list = range(args.min_length, args.max_length + 1)
        srn.generate(args.input, args.n_partitions, step_list, args.seed,
                     args.iterations, args.output)
            
    elif args.action == "simulate":
        if args.log == None:
            args.log = SRNPlan.DEF_LOGNAME(args.output)        
        srn = SRNPlan()
        srn.simulate(args.input, args.method, args.cache, args.output, args.encoding)
        
    elif args.action == "plot":
        srn = SRNPlan()        
        srn.plot_results(args.inputs, args.output, plot_integrals=True)
        
    else:
        assert(False), "Unrecognized action"
