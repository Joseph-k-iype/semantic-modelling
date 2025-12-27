"""
SQL Parser - Parse SQL DDL to extract entities and relationships
"""
from typing import List, Dict, Any
import re


class SQLParser:
    """Parser for SQL DDL statements"""
    
    def parse(self, sql: str) -> Dict[str, Any]:
        """
        Parse SQL DDL and extract table definitions
        
        Args:
            sql: SQL DDL string
            
        Returns:
            Dictionary with tables and relationships
        """
        tables = []
        relationships = []
        
        # Extract CREATE TABLE statements
        table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\((.*?)\);'
        matches = re.finditer(table_pattern, sql, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            table_name = match.group(1)
            columns_str = match.group(2)
            
            columns = self._parse_columns(columns_str)
            foreign_keys = self._parse_foreign_keys(columns_str)
            
            tables.append({
                "name": table_name,
                "columns": columns,
                "foreign_keys": foreign_keys
            })
            
            # Extract relationships from foreign keys
            for fk in foreign_keys:
                relationships.append({
                    "from_table": table_name,
                    "to_table": fk["references_table"],
                    "from_column": fk["column"],
                    "to_column": fk["references_column"],
                    "type": "foreign_key"
                })
        
        return {
            "tables": tables,
            "relationships": relationships
        }
    
    def _parse_columns(self, columns_str: str) -> List[Dict[str, Any]]:
        """Parse column definitions"""
        columns = []
        
        # Simple column parsing (can be enhanced)
        column_pattern = r'(\w+)\s+([\w()]+)(?:\s+(.+?))?(?:,|$)'
        matches = re.finditer(column_pattern, columns_str, re.IGNORECASE)
        
        for match in matches:
            column_name = match.group(1)
            data_type = match.group(2)
            constraints = match.group(3) or ""
            
            # Skip constraint lines
            if column_name.upper() in ('PRIMARY', 'FOREIGN', 'UNIQUE', 'CHECK', 'CONSTRAINT'):
                continue
            
            columns.append({
                "name": column_name,
                "type": data_type,
                "nullable": "NOT NULL" not in constraints.upper(),
                "primary_key": "PRIMARY KEY" in constraints.upper(),
                "unique": "UNIQUE" in constraints.upper()
            })
        
        return columns
    
    def _parse_foreign_keys(self, columns_str: str) -> List[Dict[str, Any]]:
        """Parse foreign key constraints"""
        foreign_keys = []
        
        # Foreign key pattern
        fk_pattern = r'FOREIGN\s+KEY\s*\((\w+)\)\s*REFERENCES\s+(\w+)\s*\((\w+)\)'
        matches = re.finditer(fk_pattern, columns_str, re.IGNORECASE)
        
        for match in matches:
            foreign_keys.append({
                "column": match.group(1),
                "references_table": match.group(2),
                "references_column": match.group(3)
            })
        
        return foreign_keys