// GENERATED from model/model.yaml — do not hand-edit. Alloy (validation Level 5).
// Finite-scope simulation: find unintended instances before they reach generated code.
// Run in Alloy Analyzer; inspect generated worlds + check the assertion.

sig Risk {}
sig Control {}
sig Person {}
sig EvidenceBundle {}
sig RiskOwner in Person {}                 // role: a Person playing RiskOwner

sig MitigationCase {
  mitigatedRisk     : some Risk,           // 1..*
  mitigatingControl : some Control,        // 1..*
  accountableOwner  : one RiskOwner,       // 1..1
  evidence          : one EvidenceBundle   // 1..1
}

// constraint: every-risk-mitigatable (IR severity: warning)
pred everyRiskMitigated { all r: Risk | some m: MitigationCase | r in m.mitigatedRisk }

// RelOver guard: the owner role must not coincide with an unrelated participant kind
fact rolesDisjointFromOtherParticipants { no (Risk & Person) and no (Control & Person) }

run everyRiskMitigated for 4
check { all m: MitigationCase | one m.accountableOwner } for 5
