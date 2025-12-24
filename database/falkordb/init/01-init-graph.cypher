// FalkorDB Initialization Script
// This script initializes the semantic graph database

// Create the main graph
GRAPH.CREATE modeling_graph

// Switch to the modeling graph
USE modeling_graph

// Create sample root nodes for testing
CREATE (:SystemNode {id: 'system-root', name: 'System Root', type: 'system', created_at: timestamp()})

// Note: Constraints and indexes are created in separate files
// This file is kept minimal to avoid initialization errors