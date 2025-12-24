// FalkorDB Indexes
// Create indexes for optimizing query performance

// ==============================================================================
// MODEL INDEXES
// ==============================================================================

// Index on Model ID for fast lookups
CREATE INDEX ON :Model(id)

// Index on Model name for searching
CREATE INDEX ON :Model(name)

// Index on Model type for filtering
CREATE INDEX ON :Model(type)

// Composite index for model queries
CREATE INDEX ON :Model(type, name)

// ==============================================================================
// CONCEPT INDEXES
// ==============================================================================

// Index on Concept ID
CREATE INDEX ON :Concept(id)

// Index on Concept name for searching
CREATE INDEX ON :Concept(name)

// Index on Concept kind for filtering
CREATE INDEX ON :Concept(kind)

// Composite index for concept queries
CREATE INDEX ON :Concept(kind, name)

// ==============================================================================
// ATTRIBUTE INDEXES
// ==============================================================================

// Index on Attribute ID
CREATE INDEX ON :Attribute(id)

// Index on Attribute name
CREATE INDEX ON :Attribute(name)

// Index on Attribute datatype
CREATE INDEX ON :Attribute(datatype)

// ==============================================================================
// UML CLASS INDEXES
// ==============================================================================

// Index on Class name
CREATE INDEX ON :Class(name)

// Index on Class stereotype
CREATE INDEX ON :Class(stereotype)

// Index on Interface name
CREATE INDEX ON :Interface(name)

// Index on Package name
CREATE INDEX ON :Package(name)

// Index on Component name
CREATE INDEX ON :Component(name)

// ==============================================================================
// UML STATE MACHINE INDEXES
// ==============================================================================

// Index on State name
CREATE INDEX ON :State(name)

// Index on State type
CREATE INDEX ON :State(stateType)

// ==============================================================================
// BPMN INDEXES
// ==============================================================================

// Index on Process ID
CREATE INDEX ON :Process(id)

// Index on Process name
CREATE INDEX ON :Process(name)

// Index on Lane name
CREATE INDEX ON :Lane(name)

// Index on Task name
CREATE INDEX ON :Task(name)

// Index on Task type
CREATE INDEX ON :Task(taskType)

// Index on Event type
CREATE INDEX ON :Event(eventType)

// Index on Gateway type
CREATE INDEX ON :Gateway(gatewayType)

// ==============================================================================
// ER INDEXES
// ==============================================================================

// Index on Entity name
CREATE INDEX ON :Entity(name)

// Index on Table name
CREATE INDEX ON :Table(name)

// Index on Table schema
CREATE INDEX ON :Table(schema)

// ==============================================================================
// LINEAGE INDEXES
// ==============================================================================

// Index on derived_from timestamp for lineage queries
CREATE INDEX ON ()-[r:DERIVED_FROM]->()(r.created_at)

// Index on impacts relationship type
CREATE INDEX ON ()-[r:IMPACTS]->()(r.impact_type)

// ==============================================================================
// CONTAINMENT INDEXES
// ==============================================================================

// Index for model containment queries
CREATE INDEX ON ()-[r:CONTAINS]->()

// Index for package containment
CREATE INDEX ON ()-[r:HAS_MEMBER]->()

// ==============================================================================
// COMPOSITE INDEXES FOR COMMON QUERIES
// ==============================================================================

// Fast lookup of concepts by model and kind
CREATE INDEX ON :Concept(model_id, kind)

// Fast lookup of attributes by concept
CREATE INDEX ON :Attribute(concept_id, name)

// ==============================================================================
// FULL-TEXT SEARCH INDEXES (if supported by FalkorDB version)
// ==============================================================================

// Note: Full-text search syntax may vary by FalkorDB version
// Uncomment if your version supports it:

// CALL db.idx.fulltext.createNodeIndex("conceptNames", ["Concept"], ["name", "description"])
// CALL db.idx.fulltext.createNodeIndex("modelNames", ["Model"], ["name", "description"])

// ==============================================================================
// NOTES
// ==============================================================================

// 1. Indexes significantly improve query performance but add overhead to writes
// 2. Monitor query performance and add indexes as needed
// 3. Composite indexes are useful for queries with multiple filters
// 4. Consider your most common query patterns when adding indexes
// 5. FalkorDB automatically uses indexes when queries match indexed properties