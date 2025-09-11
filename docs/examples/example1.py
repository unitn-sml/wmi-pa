import pysmt.shortcuts as smt

### the ReLU unit encoding

x1 = smt.Symbol("x1", smt.REAL)  # input variables
x2 = smt.Symbol("x2", smt.REAL)
xvec = [x1, x2]

h = smt.Symbol("h", smt.REAL)  # pre-activation value
y = smt.Symbol("y", smt.REAL)  # post-activation value

w1 = smt.Real(1)  # the unit (constant) parameters
w2 = smt.Real(1)
wvec = [w1, w2]

# h is the linear combination of xvec and wvec
preactivation = smt.Equals(
    h, smt.Plus(*[smt.Times(xvec[i], wvec[i]) for i in range(2)])
)

# y is max(0, h)
postactivation = smt.Ite(
    smt.LE(h, smt.Real(0)), smt.Equals(y, smt.Real(0)), smt.Equals(y, h)
)
# if-then-else: Ite(a, b, c) is shorthand for (a -> b) and (not a -> c)

unit = smt.And(preactivation, postactivation)


### PROBLEM: is the unit inactive given an interval I?

firing = smt.GT(y, smt.Real(0))

# I1: x1, x2 in [-1, 1]
I1 = smt.And(
    smt.LE(smt.Real(-1), x1),
    smt.LE(x1, smt.Real(1)),
    smt.LE(smt.Real(-1), x2),
    smt.LE(x2, smt.Real(1)),
)

# I1: x1, x2 in [-1, 0]
I2 = smt.And(
    smt.LE(smt.Real(-1), x1),
    smt.LE(x1, smt.Real(0)),
    smt.LE(smt.Real(-1), x2),
    smt.LE(x2, smt.Real(0)),
)

print("inactive in I1?", not smt.is_sat(smt.And(unit, firing, I1)))
print("inactive in I2?", not smt.is_sat(smt.And(unit, firing, I2)))

# >>> inactive in I1? False
# >>> inactive in I2? True
