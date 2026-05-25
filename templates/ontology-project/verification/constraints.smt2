; GENERATED from model/model.yaml — do not hand-edit. SMT-LIB2 (validation Level 6).
; Proves arithmetic/temporal constraints the ontology layer cannot. Check with: z3 constraints.smt2
; constraint: effective-window-ordered  ->  validFrom < validTo

(set-logic QF_LIA)
(declare-const validFrom Int)
(declare-const validTo   Int)

; assert the negation of the rule; UNSAT == the rule always holds
(assert (not (< validFrom validTo)))
(check-sat)   ; expect: sat  -> shows a counterexample exists unless validFrom<validTo is enforced upstream
(get-model)
