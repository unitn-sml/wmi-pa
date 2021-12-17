# import pysmt.operators as op
# from pysmt.walkers.generic import handles
import pysmt.walkers
from pysmt.shortcuts import *
class WeightConverter(pysmt.walkers.IdentityDagWalker):
    def __init__(self, variables, *args):
        pysmt.walkers.IdentityDagWalker.__init__(self, *args)
        self.variables = variables
        self.conv_labels = set()

    def walk_ite(self, formula, args, conversion_set=None):
        cond, left, right = args
        y = self.variables.new_weight_label(len(self.conv_labels))
        self.conv_labels.add(y)       
        conversion_set.add(Or(Not(cond), Equals(y, left)))
        conversion_set.add(Or(cond, Equals(y, right)))
        return y

    def _get_key(self, formula, **kwargs):
        return formula