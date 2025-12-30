#!/usr/bin/env python3
"""
Auto-fix all model files to use UUID instead of String(36)
This script will update all model files in backend/app/models/
"""

import os
import re
from pathlib import Path

# Fixes to apply
FIXES = {
    # Fix 1: Add UUID import if missing
    'add_uuid_import': {
        'pattern': r'from sqlalchemy import',
        'check': r'from sqlalchemy.dialects.postgresql import UUID',
        'insert_after': 'from sqlalchemy import Column',
        'insert_line': 'from sqlalchemy.dialects.postgresql import UUID, JSONB'
    },
    
    # Fix 2: Replace String(36) with UUID(as_uuid=True) for primary keys
    'fix_id_column': {
        'pattern': r'id = Column\(\s*String\(36\)',
        'replace': 'id = Column(UUID(as_uuid=True)'
    },
    
    # Fix 3: Fix uuid default for primary keys
    'fix_uuid_default': {
        'pattern': r'default=lambda: str\(uuid\.uuid4\(\)\)',
        'replace': 'default=uuid.uuid4'
    },
    
    # Fix 4: Replace String(36) ForeignKey columns
    'fix_foreign_keys': {
        'pattern': r'Column\(\s*String\(36\),\s*ForeignKey',
        'replace': 'Column(UUID(as_uuid=True), ForeignKey'
    },
    
    # Fix 5: Replace last_login with last_login_at in User model
    'fix_last_login': {
        'pattern': r'last_login = Column\(DateTime',
        'replace': 'last_login_at = Column(DateTime'
    },
    
    # Fix 6: Replace JSON with JSONB
    'fix_json': {
        'pattern': r'Column\(JSON,',
        'replace': 'Column(JSONB,'
    },
    
    # Fix 7: Replace JSON default
    'fix_json_default': {
        'pattern': r'JSON.*default=lambda: \{\}',
        'replace': 'JSONB, default=dict'
    },
}


def fix_model_file(filepath):
    """Fix a single model file"""
    print(f"\n📝 Processing: {filepath}")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    # Fix 1: Add UUID import if missing
    if 'from sqlalchemy.dialects.postgresql import UUID' not in content:
        if 'from sqlalchemy import' in content:
            content = content.replace(
                'from sqlalchemy import Column',
                'from sqlalchemy import Column\nfrom sqlalchemy.dialects.postgresql import UUID, JSONB'
            )
            changes_made.append("Added UUID and JSONB imports")
    
    # Fix 2 & 3: Fix ID columns
    if 'id = Column(String(36)' in content:
        content = re.sub(
            r'id = Column\(\s*String\(36\),\s*primary_key=True,\s*default=lambda: str\(uuid\.uuid4\(\)\)',
            'id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4',
            content
        )
        changes_made.append("Fixed id column to use UUID")
    
    # Fix 4: Fix foreign key columns
    old_fk_count = content.count('Column(String(36), ForeignKey')
    content = re.sub(
        r'Column\(\s*String\(36\),\s*ForeignKey',
        'Column(UUID(as_uuid=True), ForeignKey',
        content
    )
    new_fk_count = content.count('Column(UUID(as_uuid=True), ForeignKey')
    if new_fk_count > old_fk_count:
        changes_made.append(f"Fixed {new_fk_count - old_fk_count} foreign key columns")
    
    # Fix 5: Fix last_login in User model
    if 'last_login = Column(DateTime' in content and 'user.py' in str(filepath):
        content = content.replace(
            'last_login = Column(DateTime',
            'last_login_at = Column(DateTime'
        )
        changes_made.append("Fixed last_login to last_login_at")
    
    # Fix 6 & 7: Fix JSON to JSONB
    old_json_count = content.count('Column(JSON')
    content = content.replace('Column(JSON,', 'Column(JSONB,')
    content = re.sub(r'JSON,\s*default=lambda: \{\}', 'JSONB, default=dict', content)
    content = re.sub(r'JSON,\s*default=lambda: \[\]', 'JSONB, default=list', content)
    new_json_count = content.count('Column(JSONB')
    if new_json_count > old_json_count:
        changes_made.append(f"Converted {new_json_count - old_json_count} JSON columns to JSONB")
    
    # Write back if changes were made
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Fixed: {filepath.name}")
        for change in changes_made:
            print(f"   - {change}")
        return True
    else:
        print(f"⏭️  No changes needed: {filepath.name}")
        return False


def main():
    """Main function to fix all model files"""
    print("=" * 70)
    print("🔧 Automatic Model Fixer")
    print("=" * 70)
    print("\nThis script will automatically fix all models to use UUID types")
    print("instead of String(36), and convert JSON to JSONB.\n")
    
    # Get the models directory
    models_dir = Path('backend/app/models')
    
    if not models_dir.exists():
        print(f"❌ Error: Directory not found: {models_dir}")
        print("   Please run this script from the project root directory.")
        return 1
    
    # Find all Python files in models directory
    model_files = list(models_dir.glob('*.py'))
    model_files = [f for f in model_files if f.name not in ['__init__.py', 'base.py']]
    
    print(f"Found {len(model_files)} model files to process:\n")
    
    # Process each file
    fixed_count = 0
    for filepath in sorted(model_files):
        if fix_model_file(filepath):
            fixed_count += 1
    
    print("\n" + "=" * 70)
    print(f"✅ Complete! Fixed {fixed_count} files out of {len(model_files)} total")
    print("=" * 70)
    print("\n📋 Next steps:")
    print("1. Review the changes: git diff backend/app/models/")
    print("2. Restart backend: docker-compose -f docker-compose.dev.yml restart backend")
    print("3. Test: docker exec modeling-backend python init_database.py")
    print()
    
    return 0


if __name__ == '__main__':
    exit(main())