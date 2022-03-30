from pysmt.simplifier import Simplifier
from pysmt.shortcuts import*

class WMISimplifier(Simplifier):
    def simplify(self, formula, enable_skeleton=False):
        """Performs simplification of the given formula."""
        return self.walk(formula, enable_skeleton=enable_skeleton)

    def walk_or(self, formula, args, enable_skeleton, **kwargs):
        if len(args) == 2 and args[0] == args[1]:
            return args[0]

        new_args = set()
        for a in args:
            if a.is_false():
                continue
            if a.is_true():
                return self.manager.TRUE()
            if a.is_or():
                for s in a.args():
                    if not enable_skeleton and self.walk_not(self.manager.Not(s), [s]) in new_args:
                        return self.manager.TRUE()
                    new_args.add(s)
            else:
                if not enable_skeleton and self.walk_not(self.manager.Not(a), [a]) in new_args:
                    return self.manager.TRUE()
                new_args.add(a)

        if len(new_args) == 0:
            return self.manager.FALSE()
        elif len(new_args) == 1:
            return next(iter(new_args))
        else:
            return self.manager.Or(new_args)
