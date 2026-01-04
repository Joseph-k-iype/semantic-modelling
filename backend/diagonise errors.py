#!/usr/bin/env python3
# backend/diagnose_import_error.py
"""
Diagnose import errors in backend models
Run: docker exec modeling-backend python diagnose_import_error.py
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

print("="*80)
print("🔍 BACKEND IMPORT DIAGNOSTIC")
print("="*80)
print()

# Test imports one by one
imports_to_test = [
    ("Base", "from app.db.base import Base"),
    ("Config", "from app.core.config import settings"),
    ("User model", "from app.models.user import User, UserRole"),
    ("Workspace model", "from app.models.workspace import Workspace, WorkspaceType, WorkspaceMember, WorkspaceRole, WorkspaceInvitation, InvitationStatus"),
    ("Folder model", "from app.models.folder import Folder"),
    ("Model model", "from app.models.model import Model"),
    ("Diagram model", "from app.models.diagram import Diagram"),
    ("Layout model", "from app.models.layout import Layout, LayoutType"),
    ("Version model", "from app.models.version import Version"),
    ("Comment model", "from app.models.comment import Comment, EntityType, CommentMention, CommentReaction"),
    ("PublishWorkflow model", "from app.models.publish_workflow import PublishWorkflow, PublishWorkflowStatus"),
    ("AuditLog model", "from app.models.audit_log import AuditLog, AuditLogAction"),
    ("All models", "from app.models import *"),
    ("API Router", "from app.api.v1.router import api_router"),
    ("Main App", "from app.main import app"),
]

failed_imports = []

for name, import_statement in imports_to_test:
    print(f"Testing: {name}")
    print(f"  Statement: {import_statement}")
    try:
        exec(import_statement)
        print(f"  ✅ SUCCESS\n")
    except Exception as e:
        print(f"  ❌ FAILED")
        print(f"  Error: {type(e).__name__}: {str(e)}")
        print(f"  Full traceback:")
        import traceback
        traceback.print_exc()
        print()
        failed_imports.append((name, import_statement, e))

print("="*80)
print("SUMMARY")
print("="*80)

if not failed_imports:
    print("✅ All imports successful!")
    print("The issue might be in uvicorn configuration or environment.")
else:
    print(f"❌ {len(failed_imports)} import(s) failed:")
    print()
    for name, stmt, error in failed_imports:
        print(f"  • {name}")
        print(f"    {stmt}")
        print(f"    Error: {type(error).__name__}: {str(error)}")
        print()
    
    print("FIX REQUIRED:")
    print("1. Check the first failed import")
    print("2. Fix the file mentioned in the error")
    print("3. Re-run this diagnostic")
    print()
    print("Common issues:")
    print("  - Missing __init__.py files")
    print("  - Circular imports")
    print("  - Syntax errors in model files")
    print("  - Missing enum definitions")
    print("  - Incorrect foreign key references")

print("="*80)