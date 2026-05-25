-- GENERATED from model/model.yaml — do not hand-edit. ArcadeDB DDL (hyperedge-as-vertex).
-- The relator persists as a VERTEX joined to participants by BINDS_ROLE edges; bitemporal
-- validity + provenance live on the relator vertex (never on participants). See
-- ../../obsidian/labs/AgentArmyLabs/Reification-and-Hyperedges.md.

-- Base types
CREATE VERTEX TYPE OntologyElement IF NOT EXISTS;
CREATE VERTEX TYPE HyperNode  EXTENDS OntologyElement IF NOT EXISTS;  -- ordinary objects/aspects
CREATE VERTEX TYPE RelatorVertex EXTENDS OntologyElement IF NOT EXISTS; -- reified n-ary relations
CREATE EDGE   TYPE BINDS_ROLE IF NOT EXISTS;                          -- relator -> participant

-- Object kinds
CREATE VERTEX TYPE Risk           EXTENDS HyperNode IF NOT EXISTS;
CREATE VERTEX TYPE Control        EXTENDS HyperNode IF NOT EXISTS;
CREATE VERTEX TYPE Person         EXTENDS HyperNode IF NOT EXISTS;
CREATE VERTEX TYPE EvidenceBundle EXTENDS HyperNode IF NOT EXISTS;

-- Relator vertex with bitemporal + provenance columns
CREATE VERTEX TYPE MitigationCase EXTENDS RelatorVertex IF NOT EXISTS;
CREATE PROPERTY MitigationCase.assembledAt STRING;
CREATE PROPERTY MitigationCase.validFrom   DATETIME;
CREATE PROPERTY MitigationCase.validTo     DATETIME;
CREATE PROPERTY MitigationCase.recordedAt  DATETIME;
CREATE PROPERTY MitigationCase.supersededAt DATETIME;
CREATE PROPERTY MitigationCase.provEntity  STRING;

-- Role-binding edge metadata
CREATE PROPERTY BINDS_ROLE.roleName STRING;
CREATE PROPERTY BINDS_ROLE.ordinal  INTEGER;

-- Indexes (index-free adjacency keeps the extra hop O(1))
CREATE INDEX ON OntologyElement (ontologyIri) UNIQUE;
CREATE INDEX ON MitigationCase (validFrom, validTo) NOTUNIQUE;
CREATE INDEX ON BINDS_ROLE (roleName) NOTUNIQUE;

-- A mitigation-case instance is one vertex + four BINDS_ROLE edges:
--   (MitigationCase) -[BINDS_ROLE {roleName:'mitigatedRisk'}]->     (Risk)
--   (MitigationCase) -[BINDS_ROLE {roleName:'mitigatingControl'}]-> (Control)
--   (MitigationCase) -[BINDS_ROLE {roleName:'accountableOwner'}]->  (Person)   -- playing RiskOwner
--   (MitigationCase) -[BINDS_ROLE {roleName:'evidence'}]->          (EvidenceBundle)
-- A new version appends a new MitigationCase vertex (supersededAt set on the old); rows are never deleted.
