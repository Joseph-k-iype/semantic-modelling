// FalkorDB Constraints
// Define uniqueness and existence constraints for the semantic graph

// ==============================================================================
// MODEL CONSTRAINTS
// ==============================================================================

// Ensure Model IDs are unique
CREATE CONSTRAINT ON (m:Model) ASSERT m.id IS UNIQUE

// Ensure Models have required properties
CREATE CONSTRAINT ON (m:Model) ASSERT exists(m.id)
CREATE CONSTRAINT ON (m:Model) ASSERT exists(m.name)
CREATE CONSTRAINT ON (m:Model) ASSERT exists(m.type)

// ==============================================================================
// CONCEPT CONSTRAINTS
// ==============================================================================

// Ensure Concept IDs are unique
CREATE CONSTRAINT ON (c:Concept) ASSERT c.id IS UNIQUE

// Ensure Concepts have required properties
CREATE CONSTRAINT ON (c:Concept) ASSERT exists(c.id)
CREATE CONSTRAINT ON (c:Concept) ASSERT exists(c.kind)
CREATE CONSTRAINT ON (c:Concept) ASSERT exists(c.name)

// ==============================================================================
// ATTRIBUTE CONSTRAINTS
// ==============================================================================

// Ensure Attribute IDs are unique
CREATE CONSTRAINT ON (a:Attribute) ASSERT a.id IS UNIQUE

// Ensure Attributes have required properties
CREATE CONSTRAINT ON (a:Attribute) ASSERT exists(a.id)
CREATE CONSTRAINT ON (a:Attribute) ASSERT exists(a.name)

// ==============================================================================
// UML-SPECIFIC CONSTRAINTS
// ==============================================================================

// Class must have a name
CREATE CONSTRAINT ON (c:Class) ASSERT exists(c.name)

// Interface must have a name
CREATE CONSTRAINT ON (i:Interface) ASSERT exists(i.name)

// Package must have a name
CREATE CONSTRAINT ON (p:Package) ASSERT exists(p.name)

// ==============================================================================
// BPMN-SPECIFIC CONSTRAINTS
// ==============================================================================

// Process must have a name and ID
CREATE CONSTRAINT ON (p:Process) ASSERT exists(p.id)
CREATE CONSTRAINT ON (p:Process) ASSERT exists(p.name)

// Task must have a name
CREATE CONSTRAINT ON (t:Task) ASSERT exists(t.name)

// Event must have type
CREATE CONSTRAINT ON (e:Event) ASSERT exists(e.eventType)

// Gateway must have type
CREATE CONSTRAINT ON (g:Gateway) ASSERT exists(g.gatewayType)

// ==============================================================================
// ER-SPECIFIC CONSTRAINTS
// ==============================================================================

// Entity must have a name
CREATE CONSTRAINT ON (e:Entity) ASSERT exists(e.name)

// Table must have a name
CREATE CONSTRAINT ON (t:Table) ASSERT exists(t.name)

// ==============================================================================
// RELATIONSHIP CONSTRAINTS
// ==============================================================================

// Ensure relationship types are valid
// Note: FalkorDB uses relationship types for validation
// RELATES_TO relationships must have a kind property
CREATE CONSTRAINT ON ()-[r:RELATES_TO]-() ASSERT exists(r.kind)

// ==============================================================================
// LINEAGE CONSTRAINTS
// ==============================================================================

// Derived relationships must have metadata
CREATE CONSTRAINT ON ()-[r:DERIVED_FROM]-() ASSERT exists(r.created_at)

// Impact relationships should have type
CREATE CONSTRAINT ON ()-[r:IMPACTS]-() ASSERT exists(r.impact_type)