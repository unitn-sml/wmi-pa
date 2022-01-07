"""This module implements the parsing and dumping of raw/preprocessed datasets
for the Strategic Road Network experiment.
"""

__version__ = '0.99'
__author__ = 'Paolo Morettin'

import re
import networkx as nx
from numpy import histogram, polyfit, roots
from wmipa.latte_integrator import Latte_Integrator
from tempfile import TemporaryDirectory
from os import chdir, getcwd
from fractions import Fraction

#from integration import Integrator
from wmipa.wmiexception import WMIParsingException

class SRNParser():

    # field descriptors in the raw dataset
    EDGE_FIELD = "LinkDescription"
    TP_FIELD = "TimePeriod"
    AVGJT_FIELD = "AverageJT"
    SELECT_FIELDS = [EDGE_FIELD, TP_FIELD, AVGJT_FIELD]

    # default parameters for the distribution fitting and time partitioning
    DEF_N_PARTITIONS = 12
    MAX_TIME = 60 * 3

    ERR_FIT = "Can't fit the distribution"    

    def __init__(self, n_partitions = None):
        """Default constructor, sets the parameters for the time partitioning
        and the distribution fitting.

        Keyword arguments:
        n_partitions -- number of partitions of the day (optional)

        """
        self.integrator = Latte_Integrator()
        
        if n_partitions:
            self.n_partitions = n_partitions
        else:
            self.n_partitions = SRNParser.DEF_N_PARTITIONS

        assert(self.n_partitions < SRNParser.MAX_TIME),\
            "Number of partition cannot be smaller than 1 minute."
        
        delta = int(SRNParser.MAX_TIME / n_partitions)
        self.partitions = [(i*delta) for i in range(n_partitions)]
        self.partitions.append(SRNParser.MAX_TIME)

    @staticmethod
    def write_conditional_plan(path, plan):
        with open(path, 'w') as f:
            for src, i, dest in plan:
                nxt = plan[(src, i, dest)]
                f.write(",".join(map(str,[src, i, dest, nxt])) + "\n")

    @staticmethod
    def read_conditional_plan(path):
        plan = {}
        with open(path, 'r') as f:
            for line in f:
                try:
                    src, i, dst, nxt = line.strip().split(",")
                    i = int(i)
                    plan[(src, i, dst)] = nxt
                except ValueError:
                    continue
        return plan                

    def compute_conditional_plan(self, graph):
        msg = "Computing conditional plan: |G.nodes| = {} |G.edges| = {}"
        G = nx.DiGraph()
        n_nodes = len(graph.nodes())
        n_edges = len(graph.edges())
        print(msg.format(n_nodes, n_edges))
        computed = 0
        msg = "Computing conditional plan: building auxiliary graph G' {}/{}"
        for a, b in graph.edges():            
            print(msg.format(computed, n_edges))
            for i in range(self.n_partitions):
                pi, pf = self.partitions[i], self.partitions[i+1]
                wp = graph.get_edge_data(a,b)[i]['avg']
                next_t = ((pf - pi) / 2.0) + wp
                j = self._tp_to_partition(next_t)
                if j != None:
                    G.add_edge((a, i), (b, j), weight = wp)

            computed += 1
            
        print(msg.format(computed, n_edges))
        msg = "Computing conditional plan: |G'.nodes| = {} |G'.edges| = {}"
        print(msg.format(len(G.nodes()), len(G.edges())))
            
        print("Computing conditional plan: all-pairs Dijkstra")
        paths = dict(nx.all_pairs_dijkstra_path(G, cutoff=None))
        plan = {}

        msg = "Computing conditional plan: computing mapping from paths {}/{}"
        n_entries = self.n_partitions * (n_nodes**2)
        computed = 0

        nodes = {n for n,_ in paths}
        for src, i in paths:
            print(msg.format(computed, n_entries))
            for dst in nodes:
                lengths = []
                shortest = None
                for j in range(self.n_partitions):
                    aux_dst = (dst, j)
                    try:
                        lngt = SRNParser._length(G, paths[(src, i)][aux_dst])
                    except KeyError:
                        # reaching dst at interval j, starting from
                        # src at interval i is unfeasible.
                        continue

                    if shortest == None or lngt < shortest:
                        shortest = lngt
                        try:
                            nxt = paths[(src, i)][aux_dst][1][0]
                        except IndexError:
                            nxt = paths[(src, i)][aux_dst][0][0]
                        
                plan[(src, i, dst)] = nxt
                computed += 1
        print(msg.format(computed, n_entries))
        return plan

    @staticmethod
    def _length(graph, path):
        lngt = 0
        
        for i in range(len(path)-1):
            lngt += graph.get_edge_data(path[i], path[i+1])['weight']

        return lngt
            

    def read_raw_dataset(self, path, preprocessed_path = None):
        """Reads and preprocess a raw dataset. Since the preprocessing may
        take some time, the optional parameter 'preprocessed_path' can be
        specified in order to dump the preprocessed data for future uses.

        Keyword arguments:
        path -- the path of the raw dataset to be read
        preprocessed_path -- output path for the preprocessed data
                             (default: None)

        """
        entries = {}
        select_query = SRNParser.SELECT_FIELDS
        rows = SRNParser._read_raw_csv(path, select = select_query)
        for i, row in enumerate(rows):
            edge = SRNParser._parse_edge(row[SRNParser.EDGE_FIELD])
            # if starting point != destination
            if edge and (edge[0] != edge[1]):
                x, y = edge
                # time periods are 15 minutes long
                tp = int(row[SRNParser.TP_FIELD]) * 15
                # average journey times are expressed in seconds
                avgjt = float(row[SRNParser.AVGJT_FIELD]) / 60.0
                partition = self._tp_to_partition(tp)
                if partition == None:
                    continue
    
                if (x, y) not in entries:
                    entries[(x, y)] = {}    
                if partition not in entries[(x, y)]:
                    entries[(x, y)][partition] = [avgjt]
                else:
                    entries[(x, y)][partition].append(avgjt)
                    
        preprocessed_data = self._preprocess(entries)
        # if preprocessed_path is given, dump the aggregated data
        if preprocessed_path:
            SRNParser._write_preprocessed_data(preprocessed_path,
                                               preprocessed_data,
                                               self.partitions)

        return preprocessed_data, self.partitions

    
    @staticmethod
    def read_preprocessed_dataset(path):
        """Reads a preprocessed dataset.

        Keyword arguments:
        path -- the path of the raw dataset to be read

        """
        with open(path, "r") as f:
            preprocessed_data = {}
            partitions = None
            
            for line in f:
                if not partitions:
                    partitions = list(map(int, line.strip().split(",")))
                    
                else:
                    fields = line.strip().split(",")
                    src, dst = fields[:2]
                    part = int(fields[2])
                    avg = float(fields[3])
                    r_min, r_max = list(map(float, fields[4:6]))
                    rng = r_min, r_max
                    coeffs = list(map(float, fields[6:]))
                    if not (src, dst) in preprocessed_data:
                        preprocessed_data[(src, dst)] = {}
                    if not part in preprocessed_data[(src, dst)]:
                        preprocessed_data[(src, dst)][part] = (avg, rng, coeffs)
                    else:
                        assert(False),\
                            "Malformed file: (src, dst, partition) not unique."
                        
            return preprocessed_data, partitions

    def _fit_distribution(self, datapoints):
        frequencies, bin_edges = histogram(datapoints, bins = "sturges")
        x = [(bin_edges[i + 1] + bin_edges[i]) / 2.
             for i in range(len(bin_edges) - 1)]
        # fitting data with a quadratic polynomial
        coefficients = polyfit(x, frequencies, 2) 
        edges = [bin_edges[0], bin_edges[-1]]

        pos = (coefficients[0] > 0)
        zeros = sorted(list({z.real for z in roots(coefficients)}))
        if len(zeros) in [0, 1]:
            if pos:
                rng = edges
            else:
                print(SRNParser.ERR_FIT)
                raise WMIParsingException(SRNParser.ERR_FIT)
        elif len(zeros) == 2:
            if pos:
                # changing the 0-th order coefficient by -k
                m = (zeros[1]-zeros[0])/2.0
                a, b, c = coefficients
                k = a * (m**2) + b * m + c
                coefficients[2] += abs(k)
                rng = edges
            else:
                rng = zeros
        else:
            print(SRNParser.ERR_FIT)
            raise WMIParsingException(SRNParser.ERR_FIT)

        rng[0] = max(0, rng[0])

        # normalize the distribution
        integral = self._integrate_raw(coefficients, rng)
        if integral <= 0:
            print(SRNParser.ERR_FIT)
            raise WMIParsingException(SRNParser.ERR_FIT)
        
        coefficients = list(map(lambda c : c/integral, coefficients))
        
        return rng, coefficients
        
    def _integrate_raw(self, coefficients, rng):
        with TemporaryDirectory(dir=".") as folder:
            polynomial_file = self.integrator.POLYNOMIAL_TEMPLATE
            polytope_file = self.integrator.POLYTOPE_TEMPLATE
            output_file = self.integrator.OUTPUT_TEMPLATE        
            # change the CWD and create the temporary files
            original_cwd = getcwd()
            chdir(folder)


            frac_coeffs = list(map(Fraction, coefficients))
            with open(polynomial_file, 'w') as f:
                f.write("[[{},[2]],[{},[1]],[{},[0]]]".format(*frac_coeffs))

            b1 = Fraction(rng[0]).denominator
            b2 = Fraction(rng[1]).denominator
            bound = [-Fraction(rng[0]).numerator, b1, Fraction(rng[1]).numerator, b2]

            with open(polytope_file, 'w') as f:
                f.write("2 2\n{} {}\n{} -{}".format(*bound))       
                
            # integrate and dump the result on file
            self.integrator._call_latte(polynomial_file, polytope_file, output_file)
            # read back the result and return to the original CWD
            result = self.integrator._read_output_file(output_file)
            
            chdir(original_cwd)
        return result
        
    @staticmethod
    def _parse_edge(description):
        query = r".* between (.+) and (.+) \(.*\)"
        match = re.search(query, description)
        
        if match:
            return match.group(1), match.group(2)
        else :
            return None

    def _preprocess(self, entries):
        # build the full graph and identify the SCCs
        full_graph = nx.DiGraph()
        full_graph.add_edges_from(entries.keys())
        sccs = nx.strongly_connected_components(full_graph)

        # keep the biggest SCC
        biggest_scc = None
        size = 0
        nsccs = 0


        for scc in sccs:
            nsccs += 1
            if len(scc) > size:
                size = len(scc)
                biggest_scc = scc

        preprocessed_data = {}
        n_entries = len(entries)
        computed = 0
        msg = "Preprocessing data: {}/{}"
        
        for src, dst in entries:
            print(msg.format(computed, n_entries))
            
            if (src in biggest_scc) and (dst in biggest_scc):
                
                if not (src, dst) in preprocessed_data:
                    preprocessed_data[(src, dst)] = {}
                    
                for partition in entries[(src, dst)]:
                    avg_jts = entries[(src, dst)][partition]
                    avg = sum(avg_jts) / len(avg_jts)
                    rng, coefficients = self._fit_distribution(avg_jts)
                    entry = (avg, rng, coefficients)
                    preprocessed_data[(src, dst)][partition] = entry

            computed += 1

        return preprocessed_data

    @staticmethod
    def _read_raw_csv(path, select = None):        
        with open(path, "r") as f:
            header = f.readline().strip().split(",")

            for line in f:
                values = line.strip().split(",")
                assert(len(header) == len(values)),\
                    "Line has a different number of fields than the header"                
                yield {header[i] : values[i] for i in range(len(header))                       
                       if not select or (header[i] in select)}

    def _tp_to_partition(self, tp):        
        for i in range(self.n_partitions):
            if (self.partitions[i] <= tp) and (tp < self.partitions[i + 1]):
                return i
        return None

    @staticmethod
    def _write_preprocessed_data(path, preprocessed_data, partitions):
        with open(path, "w") as f:
            f.write(",".join(map(str, partitions)) + "\n")
            
            for src, dst in preprocessed_data:
                
                for partition in preprocessed_data[(src, dst)]:
                    entry = preprocessed_data[(src, dst)][partition]
                    avg, rng, coefficients = entry
                    f.write("{},{},{},{},{},{},{}\n".format(
                        src, dst, partition, avg, rng[0], rng[1],
                        ",".join(map(str, coefficients))))                        
