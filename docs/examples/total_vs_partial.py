import pysmt.shortcuts as smt

from wmipa.enumeration import SAEnumerator, TotalEnumerator

a = smt.Symbol("a", smt.BOOL)
b = smt.Symbol("b", smt.BOOL)
c = smt.Symbol("c", smt.BOOL)

x = smt.Symbol("x", smt.REAL)
y = smt.Symbol("y", smt.REAL)

support = smt.And(
    smt.LE(smt.Real(0), x),
    smt.LE(smt.Real(0), y),
    smt.LE(x, smt.Real(1)),
    smt.LE(y, smt.Real(1)),
    smt.Or(
        smt.GE(y, smt.Plus(x, smt.Real(1 / 4))),
        smt.LE(y, smt.Plus(x, smt.Real(-1 / 4))),
        smt.LE(smt.Plus(x, y), smt.Real(3 / 4)),
        smt.GE(smt.Plus(x, y), smt.Real(5 / 4)),
    ),
)

# support = smt.Or(a, b, c)

w = smt.Real(1)  # no weight
query = smt.Bool(True)  # no query
env = smt.get_env()  # get the pysmt enivronment

for enum_class in [TotalEnumerator, SAEnumerator]:
    enumerator = enum_class(support, w, env)
    print("----\nEnumerator:", enum_class, "\n")

    for ta, nb in enumerator.enumerate(query):
        print("TA:", ta, "\nUnassigned booleans:", nb, "\n")
