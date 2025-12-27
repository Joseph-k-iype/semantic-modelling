"""
SQL Exporter - Converts ER diagrams to SQL DDL
"""
from typing import List, Dict, Any, Set
from app.exporters.base_exporter import BaseExporter


class SQLExporter(BaseExporter):
    """Export ER diagrams to SQL DDL statements"""
    
    def export(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> str:
        """
        Convert ER diagram nodes and edges to SQL DDL
        
        Args:
            nodes: List of diagram nodes (entities)
            edges: List of diagram edges (relationships)
            
        Returns:
            SQL DDL statements as a string
        """
        sql_statements = []
        
        # Add header comment
        sql_statements.append("-- Generated SQL DDL from ER Diagram")
        sql_statements.append("-- Generated at: " + self._get_timestamp())
        sql_statements.append("")
        
        # Process entities (tables)
        entity_nodes = [n for n in nodes if n.get("type", "").startswith("ER_")]
        
        for node in entity_nodes:
            entity_data = node.get("data", {}).get("entity")
            if entity_data:
                table_sql = self._generate_create_table(entity_data)
                sql_statements.append(table_sql)
                sql_statements.append("")
        
        # Process relationships (foreign keys)
        for edge in edges:
            if edge.get("type", "") == "ER_RELATIONSHIP":
                fk_sql = self._generate_foreign_key(edge, nodes)
                if fk_sql:
                    sql_statements.append(fk_sql)
                    sql_statements.append("")
        
        # Add indexes for primary and foreign keys
        sql_statements.append("-- Indexes")
        for node in entity_nodes:
            entity_data = node.get("data", {}).get("entity")
            if entity_data:
                index_sql = self._generate_indexes(entity_data)
                if index_sql:
                    sql_statements.extend(index_sql)
                    sql_statements.append("")
        
        return "\n".join(sql_statements)
    
    def _generate_create_table(self, entity: Dict[str, Any]) -> str:
        """Generate CREATE TABLE statement for an entity"""
        table_name = self._sanitize_identifier(entity.get("name", "unknown_table"))
        attributes = entity.get("attributes", [])
        
        if not attributes:
            return f"-- WARNING: Table {table_name} has no attributes"
        
        # Start CREATE TABLE
        lines = [f"CREATE TABLE {table_name} ("]
        
        # Add columns
        column_definitions = []
        primary_keys = []
        
        for attr in attributes:
            col_name = self._sanitize_identifier(attr.get("name", "column"))
            col_type = attr.get("type", "VARCHAR(255)")
            
            # Build column definition
            col_def = f"    {col_name} {col_type}"
            
            # Add constraints
            if not attr.get("isNullable", True):
                col_def += " NOT NULL"
            
            if attr.get("isUnique", False):
                col_def += " UNIQUE"
            
            if attr.get("defaultValue"):
                col_def += f" DEFAULT {attr['defaultValue']}"
            
            column_definitions.append(col_def)
            
            # Track primary keys
            if attr.get("isPrimary", False):
                primary_keys.append(col_name)
        
        # Add column definitions to table
        lines.extend([f"{col}," for col in column_definitions])
        
        # Add primary key constraint
        if primary_keys:
            pk_constraint = f"    PRIMARY KEY ({', '.join(primary_keys)})"
            lines.append(pk_constraint)
        else:
            # Remove trailing comma from last column
            if lines[-1].endswith(","):
                lines[-1] = lines[-1][:-1]
        
        lines.append(");")
        
        return "\n".join(lines)
    
    def _generate_foreign_key(
        self,
        edge: Dict[str, Any],
        nodes: List[Dict[str, Any]]
    ) -> str:
        """Generate ALTER TABLE statement for foreign key"""
        source_id = edge.get("source")
        target_id = edge.get("target")
        
        # Find source and target entities
        source_node = next((n for n in nodes if n.get("id") == source_id), None)
        target_node = next((n for n in nodes if n.get("id") == target_id), None)
        
        if not source_node or not target_node:
            return ""
        
        source_entity = source_node.get("data", {}).get("entity")
        target_entity = target_node.get("data", {}).get("entity")
        
        if not source_entity or not target_entity:
            return ""
        
        source_table = self._sanitize_identifier(source_entity.get("name", ""))
        target_table = self._sanitize_identifier(target_entity.get("name", ""))
        
        # Find primary key of target table
        target_pk = None
        for attr in target_entity.get("attributes", []):
            if attr.get("isPrimary", False):
                target_pk = self._sanitize_identifier(attr.get("name", ""))
                break
        
        if not target_pk:
            return f"-- WARNING: No primary key found for {target_table}"
        
        # Create foreign key column name
        fk_column = f"{target_table}_id"
        
        # Generate ALTER TABLE statement
        sql = f"""ALTER TABLE {source_table}
    ADD COLUMN {fk_column} VARCHAR(255),
    ADD CONSTRAINT fk_{source_table}_{target_table}
    FOREIGN KEY ({fk_column})
    REFERENCES {target_table}({target_pk})
    ON DELETE CASCADE;"""
        
        return sql
    
    def _generate_indexes(self, entity: Dict[str, Any]) -> List[str]:
        """Generate CREATE INDEX statements for an entity"""
        table_name = self._sanitize_identifier(entity.get("name", ""))
        attributes = entity.get("attributes", [])
        
        indexes = []
        
        for attr in attributes:
            # Create index for unique columns
            if attr.get("isUnique", False) and not attr.get("isPrimary", False):
                col_name = self._sanitize_identifier(attr.get("name", ""))
                index_name = f"idx_{table_name}_{col_name}"
                indexes.append(
                    f"CREATE UNIQUE INDEX {index_name} ON {table_name}({col_name});"
                )
            
            # Create index for foreign key columns
            if attr.get("isForeign", False):
                col_name = self._sanitize_identifier(attr.get("name", ""))
                index_name = f"idx_{table_name}_{col_name}"
                indexes.append(
                    f"CREATE INDEX {index_name} ON {table_name}({col_name});"
                )
        
        return indexes
    
    def _sanitize_identifier(self, identifier: str) -> str:
        """
        Sanitize SQL identifier (remove special characters, ensure valid name)
        """
        # Remove special characters and replace spaces with underscores
        sanitized = "".join(c if c.isalnum() or c == "_" else "_" for c in identifier)
        
        # Ensure doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = "_" + sanitized
        
        # Convert to lowercase for consistency
        return sanitized.lower()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string"""
        from datetime import datetime
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")