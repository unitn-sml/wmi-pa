#!/usr/bin/python

import sys
import os
import argparse

from wmipa.parser import MinizincParser, SmtlibParser
from wmipa import WMI


def main():
    parser = argparse.ArgumentParser(description='Computes WMI (Weighted Model Integration) given a model and some queries')
    parser.add_argument('files', nargs='+', help='If one file is provided, it must contain the model of WMI \
        and also all the queries, otherwise the first file will be considered as model and the reamining as queries (all files in .smt or .mzn format)')
    parser.add_argument('-i', '--integrations', action='store_true', help='Output also the number of integrations')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-o', '--output', nargs=1, dest='output', help='The output file')
    group.add_argument('-os', '--output-suffix', nargs=1, dest='output_suffix', help='The suffix to add to the query file name in order to get the output file name')
    group.add_argument('-ol', '--output-list', nargs='+', dest='output_list', help='The list of output files (one for each query)')
    args = parser.parse_args()
    
    files = args.files
    show_int = args.integrations
    output = args.output
    output_suffix = args.output_suffix
    output_list = args.output_list
    
    query_list = files[1:]
    
    # check number of query and of output files
    if output_list and len(output_list) != len(query_list):
        print(parser.prog+": error:", "The number of output files must be equal to the number of query files")
        sys.exit(2)
        
    # check suffix and at least one query file
    if output_suffix and len(query_list) < 1:
        print(parser.prog+": error:", "The output suffix requires at least one query file")
        sys.exit(2)
        
    # check name of output files do not collide
    if output_list:
        no_dup = list(set(output_list))
        if len(output_list) != len(no_dup):
            print(parser.prog+": error:", "The name of output files must be all differents")
            sys.exit(2)
            
    # check query files all differents
    no_dup = list(set(query_list))
    if len(no_dup) != len(query_list):
        print(parser.prog+": warning:", "Repetion of query file")
        
    wmi = None
    domA = None
    domX = None
    batch_of_queries = []
    batch_of_results = []
       
    if len(files) > 1:
        model = files[0]
        model_name, model_extension = os.path.splitext(model)
            
        # check that model file is minizinc or smtlib format
        if model_extension == '.mzn':
            support, weight, domA, domX = MinizincParser.parseModel(model)
        elif model_extension == '.smt':
            support, weight, domA, domX = SmtlibParser.parseModel(model)
        else:
            print('Model file must be .mzn or .smt ({})'.format(model))
            sys.exit(1)
            
        # create wmi instance
        wmi = WMI(support, weight)
            
        # take queries
        for query_file in query_list:
            query_name, query_extension = os.path.splitext(query_file)
        
            # check that query file is minizinc or smtlib format
            if query_extension == '.mzn':
                batch_of_queries.append(MinizincParser.parseQuery(query_file, domA, domX))
            elif query_extension == '.smt':
                batch_of_queries.append(SmtlibParser.parseQuery(query_file, domA, domX))
            else:
                print('Query file must be .mzn or .smt ({})'.format(query_file))
                sys.exit(1)
        
    else:
        complete = files[0]
        complete_name, complete_extension = os.path.splitext(complete)
        
        # check that complete file is minizinc or smtlib format
        if complete_extension == '.mzn':
            support, weight, domA, domX, queries = MinizincParser.parseAll(complete)
        elif complete_extension == '.smt':
            support, weight, domA, domX, queries = SmtlibParser.parseAll(complete)
        else:
            print('Complete file must be .mzn or .smt ({})'.format(model))
            sys.exit(1)
            
        # create wmi instance
        wmi = WMI(support, weight)
        
        batch_of_queries = [queries]
        
    for queries in batch_of_queries:
        # compute wmi on all the queries
        results, integrations = wmi.computeWMI_batch(queries, domA=set(domA), domX=domX)
        
        batch_of_results.append((results, integrations))
    
    # create output list with suffix
    if output_suffix:
        suffix = output_suffix[0]
        output_list = []
        
        for i in range(len(query_list)):
            query = query_list[i]
            filename, file_extension = os.path.splitext(query)
            output_list.append('{}{}{}.txt'.format(filename, suffix, file_extension))
    
    # output result...
    # on one file
    if output:
        with open(output[0], 'w') as f:
            for results, integrations in batch_of_results:
                f.write(out(results, integrations, show_int)+'\n')
                
    # on list of files
    elif output_list:
        for i in range(len(batch_of_results)):
            results, integrations = batch_of_results[i]
            with open(output_list[i], 'w') as f:
                f.write(out(results, integrations, show_int))
    
    # on console
    else:
        for results, integrations in batch_of_results:
            print(out(results, integrations, show_int))
            
            
def out(results, integrations, show_int):
    ret = ''
    for i in range(len(results)):
        if show_int:
            ret = ret+ '{}, {}\n'.format(results[i], integrations[i])
        else:
            ret = ret+ '{}\n'.format(results[i])
    return ret
        
            
if __name__ == "__main__":
    main()
