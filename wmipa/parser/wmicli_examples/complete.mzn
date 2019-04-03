var float:x;
var 0.0..2.0:y;

weight : if y < 1 then x+y else 2*y endif;

constraint (  y<1       -> (x>0 /\ x<2)  )
        /\ (  not (y<1) -> (x>1 /\ x<3)  );
        
query (x>1.5);
query (x<1.5);
query (true);

/* 
chi = And(Implies(LE(y, Real(1)), And(LE(Real(0), x), LE(x, Real(2)))),
          Implies(Not(LE(y, Real(1))), And(LE(Real(1), x), LE(x, Real(3)))),
          LE(Real(0), y), LE(y, Real(2)))

w = Ite(LE(y, Real(1)),
        Plus(x, y),
        Times(Real(2),y))
        
phi1 = GE(x, Real(1.5))
phi2 = LE(x, Real(1.5))
phi3 = Bool(True)
*/
