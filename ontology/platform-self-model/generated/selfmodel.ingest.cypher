// constraints
[
  "CREATE CONSTRAINT ArchitecturalDecision_constraint IF NOT EXISTS FOR (n:ArchitecturalDecision) REQUIRE (n.architecturaldecisionId) IS NODE KEY;",
  "CREATE CONSTRAINT Agent_constraint IF NOT EXISTS FOR (n:Agent) REQUIRE (n.agentId) IS NODE KEY;",
  "CREATE CONSTRAINT Contract_constraint IF NOT EXISTS FOR (n:Contract) REQUIRE (n.contractId) IS NODE KEY;",
  "CREATE CONSTRAINT ExternalOrganization_constraint IF NOT EXISTS FOR (n:ExternalOrganization) REQUIRE (n.externalorganizationId) IS NODE KEY;",
  "CREATE CONSTRAINT Army_constraint IF NOT EXISTS FOR (n:Army) REQUIRE (n.armyId) IS NODE KEY;",
  "CREATE CONSTRAINT SpokeRepository_constraint IF NOT EXISTS FOR (n:SpokeRepository) REQUIRE (n.spokerepositoryId) IS NODE KEY;",
  "CREATE CONSTRAINT ApplicationContainer_constraint IF NOT EXISTS FOR (n:ApplicationContainer) REQUIRE (n.applicationcontainerId) IS NODE KEY;",
  "CREATE CONSTRAINT HubRepository_constraint IF NOT EXISTS FOR (n:HubRepository) REQUIRE (n.hubrepositoryId) IS NODE KEY;",
  "CREATE CONSTRAINT governed_by_decision_constraint IF NOT EXISTS FOR (n:governed_by_decision) REQUIRE (n.governed_by_decisionId) IS NODE KEY;",
  "CREATE CONSTRAINT PlatformContainer_constraint IF NOT EXISTS FOR (n:PlatformContainer) REQUIRE (n.platformcontainerId) IS NODE KEY;",
  "CREATE CONSTRAINT partner_engagement_constraint IF NOT EXISTS FOR (n:partner_engagement) REQUIRE (n.partner_engagementId) IS NODE KEY;",
  "CREATE CONSTRAINT Capability_constraint IF NOT EXISTS FOR (n:Capability) REQUIRE (n.capabilityId) IS NODE KEY;",
  "CREATE CONSTRAINT FunctionContainer_constraint IF NOT EXISTS FOR (n:FunctionContainer) REQUIRE (n.functioncontainerId) IS NODE KEY;",
  "CREATE CONSTRAINT contract_binding_constraint IF NOT EXISTS FOR (n:contract_binding) REQUIRE (n.contract_bindingId) IS NODE KEY;",
  "CREATE CONSTRAINT Container_constraint IF NOT EXISTS FOR (n:Container) REQUIRE (n.containerId) IS NODE KEY;",
  "CREATE CONSTRAINT SystemComponent_constraint IF NOT EXISTS FOR (n:SystemComponent) REQUIRE (n.systemcomponentId) IS NODE KEY;",
  "CREATE CONSTRAINT capability_realization_constraint IF NOT EXISTS FOR (n:capability_realization) REQUIRE (n.capability_realizationId) IS NODE KEY;",
  "CREATE CONSTRAINT release_delivery_constraint IF NOT EXISTS FOR (n:release_delivery) REQUIRE (n.release_deliveryId) IS NODE KEY;",
  "CREATE CONSTRAINT Repository_constraint IF NOT EXISTS FOR (n:Repository) REQUIRE (n.repositoryId) IS NODE KEY;",
  "CREATE CONSTRAINT Platform_constraint IF NOT EXISTS FOR (n:Platform) REQUIRE (n.platformId) IS NODE KEY;",
  "CREATE CONSTRAINT deployment_constraint IF NOT EXISTS FOR (n:deployment) REQUIRE (n.deploymentId) IS NODE KEY;",
  "CREATE CONSTRAINT ReleaseTrain_constraint IF NOT EXISTS FOR (n:ReleaseTrain) REQUIRE (n.releasetrainId) IS NODE KEY;"
]

// sample node ingest
UNWIND $records as record
MERGE (n: ArchitecturalDecision {architecturaldecisionId: record.architecturaldecisionId})
SET n += {}
