"""
Development validation utilities to catch common issues early.

Run these checks during development to prevent runtime errors.
"""

import sys
import importlib
from typing import List, Dict, Any
from pathlib import Path


def check_python_compatibility() -> List[str]:
    """Check Python version compatibility."""
    issues = []

    if sys.version_info < (3, 11):
        issues.append(f"Python {sys.version_info.major}.{sys.version_info.minor} detected. Minimum Python 3.11 required.")

    return issues


def check_uuid_usage() -> List[str]:
    """Check for common UUID-related issues."""
    issues = []

    try:
        from uuid import UUID

        # Test UUID creation methods
        test_uuid = UUID(int=0x12345678123456781234567812345678)
        if not hasattr(UUID, 'int'):
            issues.append("UUID(int=...) constructor not available")

        # Check if _from_int exists (it shouldn't in modern Python)
        if hasattr(UUID, '_from_int'):
            issues.append("WARNING: UUID._from_int() detected - use UUID(int=...) instead")

    except Exception as e:
        issues.append(f"UUID import/usage error: {e}")

    return issues


def check_enum_consistency(model_file: str = "db/models.py") -> List[str]:
    """Check that enum values follow lowercase convention."""
    issues = []

    try:
        models_path = Path(__file__).parent.parent / model_file
        if models_path.exists():
            content = models_path.read_text()

            # Look for enum definitions
            lines = content.split('\n')
            in_enum = False
            enum_name = ""

            for i, line in enumerate(lines):
                stripped = line.strip()

                if 'class' in stripped and 'Enum' in stripped:
                    in_enum = True
                    enum_name = stripped.split()[1].split('(')[0]
                    continue

                if in_enum and stripped == "":
                    in_enum = False
                    continue

                if in_enum and '=' in stripped:
                    # Check enum value
                    parts = stripped.split('=')
                    if len(parts) == 2:
                        value = parts[1].strip().strip('"\'')
                        if value != value.lower():
                            issues.append(f"Enum {enum_name}: '{value}' should be lowercase for database compatibility")

    except Exception as e:
        issues.append(f"Could not check enum consistency: {e}")

    return issues


def check_temporal_patterns(workflows_dir: str = "workflows/") -> List[str]:
    """Check for common Temporal workflow issues."""
    issues = []

    try:
        workflows_path = Path(__file__).parent.parent / workflows_dir
        if workflows_path.exists():
            for py_file in workflows_path.glob("*.py"):
                content = py_file.read_text()

                # Check for asyncio.sleep in workflows
                if "asyncio.sleep" in content and "@workflow.defn" in content:
                    issues.append(f"{py_file.name}: Use workflow.sleep() not asyncio.sleep() in workflows")

                # Check for wait_condition usage
                if "wait_condition" in content:
                    # Look for common wait_condition logic errors
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if "wait_condition" in line and "lambda:" in line:
                            # Check next few lines for proper handling
                            next_lines = lines[i+1:i+10]
                            next_text = '\n'.join(next_lines)
                            if "if not" in next_text and "wait_condition" not in next_text:
                                issues.append(f"{py_file.name}:{i+1}: Possible wait_condition logic error - check boolean handling")

    except Exception as e:
        issues.append(f"Could not check Temporal patterns: {e}")

    return issues


def check_database_types() -> List[str]:
    """Check for common database type issues."""
    issues = []

    try:
        # Check if pk_field returns string type
        from ..db.utils import pk_field
        field = pk_field()

        # This is a basic check - in practice you'd want more sophisticated validation
        if not hasattr(field, 'default_factory'):
            issues.append("pk_field() should have default_factory for UUID generation")

    except Exception as e:
        issues.append(f"Could not check database types: {e}")

    return issues


def run_all_checks() -> Dict[str, List[str]]:
    """Run all validation checks and return results."""
    return {
        "python_compatibility": check_python_compatibility(),
        "uuid_usage": check_uuid_usage(),
        "enum_consistency": check_enum_consistency(),
        "temporal_patterns": check_temporal_patterns(),
        "database_types": check_database_types(),
    }


def print_validation_report():
    """Print a formatted validation report."""
    print("🔍 Running development validation checks...\n")

    results = run_all_checks()
    total_issues = sum(len(issues) for issues in results.values())

    for category, issues in results.items():
        status = "✅" if not issues else "❌"
        print(f"{status} {category.replace('_', ' ').title()}")

        for issue in issues:
            print(f"  • {issue}")

        if not issues:
            print("  • No issues found")

        print()

    if total_issues == 0:
        print("🎉 All validation checks passed!")
    else:
        print(f"⚠️  Found {total_issues} potential issues. Review and fix before deployment.")

    return total_issues


if __name__ == "__main__":
    import sys
    exit_code = 1 if print_validation_report() > 0 else 0
    sys.exit(exit_code)