from pysmt.shortcuts import *
from pysmt.typing import REAL, BOOL
from wmipa import WMI

a = Symbol("A", BOOL)
b = Symbol("B", BOOL)
c = Symbol("C", BOOL)
x = Symbol("x", REAL)
y = Symbol("y", REAL)
z = Symbol("z", REAL)
phi = Bool(True)

def test_no_booleans_constant_weight():
    chi = And(GE(x, Real(0)),
              LE(x, Real(1)))
      
    wmi = WMI(chi)      
    
    result_bc, _ = wmi.computeMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeMI(phi, mode=WMI.MODE_PA)
    result_pa_nl, _ = wmi.computeMI(phi, mode=WMI.MODE_PA_NO_LABEL)
    result_pa_euf, _ = wmi.computeMI(phi, mode=WMI.MODE_PA_EUF)
    result_pa_euf_ta, _ = wmi.computeMI(phi, mode=WMI.MODE_PA_EUF_TA)
    assert result_bc == 1
    assert result_allsmt == 1
    assert result_pa == 1
    assert result_pa_nl == 1
    assert result_pa_euf == 1
    assert result_pa_euf_ta == 1
    
def test_no_booleans_condition_weight():
    chi = And(GE(x, Real(0)),
              LE(x, Real(1)))
              
    w = Ite(LE(x, Real(0.5)), x, Times(Real(-1), x))
    
    wmi = WMI(chi, w)      
    
    result_bc, _ = wmi.computeWMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeWMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA)
    result_pa_nl, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_NO_LABEL)
    result_pa_euf, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_EUF)
    result_pa_euf_ta, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_EUF_TA)
    assert result_bc == -0.25
    assert result_allsmt == -0.25
    assert result_pa == -0.25
    assert result_pa_nl == -0.25
    assert result_pa_euf == -0.25
    assert result_pa_euf_ta == -0.25
    
def test_booleans_constant_weight():
    chi = And(Iff(a, GE(x, Real(0))),
              GE(x, Real(-2)),
              LE(x, Real(1)))
    
    wmi = WMI(chi)      
    
    result_bc, _ = wmi.computeMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeMI(phi, mode=WMI.MODE_PA)
    result_pa_nl, _ = wmi.computeMI(phi, mode=WMI.MODE_PA_NO_LABEL)
    result_pa_euf, _ = wmi.computeMI(phi, mode=WMI.MODE_PA_EUF)
    result_pa_euf_ta, _ = wmi.computeMI(phi, mode=WMI.MODE_PA_EUF_TA)
    assert result_bc == 3
    assert result_allsmt == 3
    assert result_pa == 3
    assert result_pa_nl == 3
    assert result_pa_euf == 3
    assert result_pa_euf_ta == 3
    
def test_boolean_condition_weight():
    chi = And(Iff(a, GE(x, Real(0))),
              GE(x, Real(-1)),
              LE(x, Real(1)))
              
    w = Ite(LE(x, Real(-0.5)), x, Ite(a, Times(Real(-1), x), Times(Real(2), x)))
    
    wmi = WMI(chi, w)      
    
    result_bc, _ = wmi.computeWMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeWMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA)
    result_pa_nl, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_NO_LABEL)
    result_pa_euf, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_EUF)
    result_pa_euf_ta, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_EUF_TA)
    assert result_bc == -1.125
    assert result_allsmt == -1.125
    assert result_pa == -1.125
    assert result_pa_nl == -1.125
    assert result_pa_euf == -1.125
    assert result_pa_euf_ta == -1.125
    
def test_boolean_and_not_simplify():
    chi = And(Iff(a, GE(x, Real(0))),
              Or(And(GE(x, Real(-3)), LE(x, Real(-2))),
                 And(GE(x, Real(-1)), LE(x, Real(1))),
                 And(GE(x, Real(2)), LE(x, Real(3)))))
              
    w = Ite(LE(x, Real(-0.5)), x, Ite(a, Times(Real(-1), x), Times(Real(2), x)))
    
    wmi = WMI(chi, w)      
    
    result_bc, _ = wmi.computeWMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeWMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA)
    result_pa_nl, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_NO_LABEL)
    result_pa_euf, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_EUF)
    result_pa_euf_ta, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_EUF_TA)
    assert result_bc == -6.125
    assert result_allsmt == -6.125
    assert result_pa == -6.125
    assert result_pa_nl == -6.125
    assert result_pa_euf == -6.125
    assert result_pa_euf_ta == -6.125
    
def test_not_boolean_satisfiable():
    chi = And(Iff(a, GE(x, Real(0))),
              GE(x, Real(-1)),
              LE(x, Real(1)),
              b,
              Not(b))

    w = Ite(b, x, Ite(a, Times(Real(-1), x), Times(Real(2), x)))
    
    wmi = WMI(chi, w)      
    
    result_bc, _ = wmi.computeWMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeWMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA)
    result_pa_nl, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_NO_LABEL)
    result_pa_euf, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_EUF)
    result_pa_euf_ta, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_EUF_TA)
    assert result_bc == 0
    assert result_allsmt == 0
    assert result_pa == 0
    assert result_pa_nl == 0
    assert result_pa_euf == 0
    assert result_pa_euf_ta == 0
    
def test_not_lra_satisfiable():
    chi = And(Iff(a, GE(x, Real(0))),
              GE(x, Real(-1)),
              LE(x, Real(1)),
              GE(x, Real(2)))

    w = Ite(b, x, Ite(a, Times(Real(-1), x), Times(Real(2), x)))
    
    wmi = WMI(chi, w)      
    
    result_bc, _ = wmi.computeWMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeWMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA)
    result_pa_nl, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_NO_LABEL)
    result_pa_euf, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_EUF)
    result_pa_euf_ta, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_EUF_TA)
    assert result_bc == 0
    assert result_allsmt == 0
    assert result_pa == 0
    assert result_pa_nl == 0
    assert result_pa_euf == 0
    assert result_pa_euf_ta == 0

def test_moltiplication_in_weight():
    chi = And(Iff(a, GE(x, Real(0))),
              Or(And(GE(x, Real(-3)), LE(x, Real(-2))),
                 And(GE(x, Real(-1)), LE(x, Real(1))),
                 And(GE(x, Real(2)), LE(x, Real(3)))))
                 
    w = Times(Ite(a, x, Times(x, Real(-1))), x)
    
    wmi = WMI(chi, w)      
    
    result_bc, _ = wmi.computeWMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeWMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA)
    result_pa_nl, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_NO_LABEL)
    result_pa_euf, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_EUF)
    result_pa_euf_ta, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_EUF_TA)
    assert result_bc == 0
    assert result_allsmt == 0
    assert result_pa == 0
    assert result_pa_nl == 0
    assert result_pa_euf == 0
    assert result_pa_euf_ta == 0

def test_aliases():
    chi = And(GE(x, Real(0)), Equals(y, Plus(x, Real(-2))), LE(y, Real(4)))
    
    w = y
    
    wmi = WMI(chi, w)      
    
    result_bc, _ = wmi.computeWMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeWMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA)
    result_pa_nl, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_NO_LABEL)
    result_pa_euf, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_EUF)
    result_pa_euf_ta, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_EUF_TA)
    assert result_bc == 6
    assert result_allsmt == 6
    assert result_pa == 6
    assert result_pa_nl == 6
    assert result_pa_euf == 6
    assert result_pa_euf_ta == 6
    
def test_aliases_leads_to_not_sat():
    chi = And(GE(x, Real(0)), LE(x, Real(2)), Equals(y, x), LE(x-y, Real(-2)))
    
    wmi = WMI(chi)
    
    result_bc, _ = wmi.computeMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeMI(phi, mode=WMI.MODE_PA)
    result_pa_nl, _ = wmi.computeMI(phi, mode=WMI.MODE_PA_NO_LABEL)
    result_pa_euf, _ = wmi.computeMI(phi, mode=WMI.MODE_PA_EUF)
    result_pa_euf_ta, _ = wmi.computeMI(phi, mode=WMI.MODE_PA_EUF_TA)
    assert result_bc == 0
    assert result_allsmt == 0
    assert result_pa == 0
    assert result_pa_nl == 0
    assert result_pa_euf == 0
    assert result_pa_euf_ta == 0
    
def test_batch_of_query_constant_weight():
    chi = And(GE(x, Real(0)),
              LE(x, Real(4)))
    
    phi1 = LE(x, Real(2))
    phi2 = GE(x, Real(2))
    
    wmi = WMI(chi)
    
    result_bc, _ = wmi.computeMI_batch([phi1, phi2], mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeMI_batch([phi1, phi2], mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeMI_batch([phi1, phi2], mode=WMI.MODE_PA)
    result_pa_nl, _ = wmi.computeMI_batch([phi1, phi2], mode=WMI.MODE_PA_NO_LABEL)
    result_pa_euf, _ = wmi.computeMI_batch([phi1, phi2], mode=WMI.MODE_PA_EUF)
    result_pa_euf_ta, _ = wmi.computeMI_batch([phi1, phi2], mode=WMI.MODE_PA_EUF_TA)
    assert result_bc[0] == 2
    assert result_bc[1] == 2
    assert result_allsmt[0] == 2
    assert result_allsmt[1] == 2
    assert result_pa[0] == 2
    assert result_pa[1] == 2
    assert result_pa_nl[0] == 2
    assert result_pa_nl[1] == 2
    assert result_pa_euf[0] == 2
    assert result_pa_euf[1] == 2
    assert result_pa_euf_ta[0] == 2
    assert result_pa_euf_ta[1] == 2
    
def test_batch_of_query():
    chi = And(GE(x, Real(0)),
              LE(x, Real(2)))
    
    phi1 = LE(x, Real(1))
    phi2 = GE(x, Real(1))
    
    w = x
    
    wmi = WMI(chi, w)
    
    result_bc, _ = wmi.computeWMI_batch([phi1, phi2], mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeWMI_batch([phi1, phi2], mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeWMI_batch([phi1, phi2], mode=WMI.MODE_PA)
    result_pa_nl, _ = wmi.computeWMI_batch([phi1, phi2], mode=WMI.MODE_PA_NO_LABEL)
    result_pa_euf, _ = wmi.computeWMI_batch([phi1, phi2], mode=WMI.MODE_PA_EUF)
    result_pa_euf_ta, _ = wmi.computeWMI_batch([phi1, phi2], mode=WMI.MODE_PA_EUF_TA)
    assert result_bc[0] == 0.5
    assert result_bc[1] == 1.5
    assert result_allsmt[0] == 0.5
    assert result_allsmt[1] == 1.5
    assert result_pa[0] == 0.5
    assert result_pa[1] == 1.5
    assert result_pa_nl[0] == 0.5
    assert result_pa_nl[1] == 1.5
    assert result_pa_euf[0] == 0.5
    assert result_pa_euf[1] == 1.5
    assert result_pa_euf_ta[0] == 0.5
    assert result_pa_euf_ta[1] == 1.5
    
def test_setting_domA():
    chi = And(GE(x, Real(0)),
              LE(x, Real(2)),
              a)
              
    wmi = WMI(chi)
    result_bc, _ = wmi.computeMI(phi, mode=WMI.MODE_BC, domA=set([a, b]))
    result_allsmt, _ = wmi.computeMI(phi, mode=WMI.MODE_ALLSMT, domA=set([a, b]))
    result_pa, _ = wmi.computeMI(phi, mode=WMI.MODE_PA, domA=set([a, b]))
    result_pa_nl, _ = wmi.computeMI(phi, mode=WMI.MODE_PA_NO_LABEL, domA=set([a, b]))
    result_pa_euf, _ = wmi.computeMI(phi, mode=WMI.MODE_PA_EUF, domA=set([a, b]))
    result_pa_euf_ta, _ = wmi.computeMI(phi, mode=WMI.MODE_PA_EUF_TA, domA=set([a, b]))
    assert result_bc == 2*2
    assert result_allsmt == 2*2
    assert result_pa == 2*2
    assert result_pa_nl == 2*2
    assert result_pa_euf == 2*2
    assert result_pa_euf_ta == 2*2
    
def test_double_assignment_same_variable_no_theory_consistent():
    chi = And(GE(x, Real(0)), Equals(y, Plus(x, Real(-2))), Equals(y, Plus(x, Real(5))), LE(y, Real(4)))
    
    wmi = WMI(chi)
    
    result_bc, _ = wmi.computeMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeMI(phi, mode=WMI.MODE_PA)
    result_pa_nl, _ = wmi.computeMI(phi, mode=WMI.MODE_PA_NO_LABEL)
    result_pa_euf, _ = wmi.computeMI(phi, mode=WMI.MODE_PA_EUF)
    result_pa_euf_ta, _ = wmi.computeMI(phi, mode=WMI.MODE_PA_EUF_TA)
    assert result_bc == 0
    assert result_allsmt == 0
    assert result_pa == 0
    assert result_pa_nl == 0
    assert result_pa_euf == 0
    assert result_pa_euf_ta == 0

def test_reserved_variables_name():
    a = Symbol("wmi_1_a", BOOL)
    b = Symbol("cond_a", BOOL)
    x = Symbol("query_45", REAL)
    y = FreshSymbol(REAL)
    
    chi = And(GE(x, Real(0)), LE(x, Real(2)),
              GE(y, Real(2)), LE(y, Real(4)),
              Iff(a, LE(x, Real(1))),
              Iff(b, LE(y, Real(3))))
              
    w = Ite(a, x, y)
    
    wmi = WMI(chi, w)
    
    result_bc, abc = wmi.computeWMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeWMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA)
    result_pa_nl, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_NO_LABEL)
    result_pa_euf, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_EUF)
    result_pa_euf_ta, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA_EUF_TA)
    assert result_bc == 7
    assert result_allsmt == 7
    assert result_pa == 7
    assert result_pa_nl == 7
    assert result_pa_euf == 7
    assert result_pa_euf_ta == 7
