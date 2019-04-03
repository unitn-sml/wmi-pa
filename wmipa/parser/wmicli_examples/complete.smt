(declare-fun x() Real)
(declare-fun y() Real)

(assert (>= y 0))
(assert (<= y 2))

(weight (ite (< y 1) (+ x y) (* 2 y)))

(assert (=> (< y 1) (and (> x 0) (< x 2))))
(assert (=> (not (< y 1)) (and (> x 1) (< x 3))))

(query (>= x 1.5))
(query (<= x 1.5))
(query true)

;chi = And(Implies(LE(y, Real(1)), And(LE(Real(0), x), LE(x, Real(2)))),
;          Implies(Not(LE(y, Real(1))), And(LE(Real(1), x), LE(x, Real(3)))),
;          LE(Real(0), y), LE(y, Real(2)))

;w = Ite(LE(y, Real(1)),
;        Plus(x, y),
;        Times(Real(2),y))

;phi1 = GE(x, Real(1.5))
;phi2 = LE(x, Real(1.5))
;phi3 = Bool(True)
