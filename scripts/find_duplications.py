#!/usr/bin/env python3
"""
Script to find code duplication patterns in the codebase.
Helps identify blocks that can be extracted to utility functions.
"""
import ast
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Patterns that are commonly duplicated
DUPLICATION_PATTERNS = [
    (r"raise SynapseError\(400,.*?\)", "SynapseError 400 patterns"),
    (r"try:\s*\n.*?except.*?SynapseError", "Error handling with SynapseError"),
    (r"if not .*?:\s*\n\s*raise SynapseError", "Validation with SynapseError"),
    (r"await.*?\.get.*?\(.*?\)", "Database query patterns"),
    (r"logger\.(error|warning|info|debug)\(.*?\)", "Logging patterns"),
    (r"return \{.*?errcode.*?\}", "Error response formatting"),
    (r"@attr\.s.*?class.*?:", "Attr classes with similar structure"),
]


def find_pattern_in_file(file_path: Path, pattern: str, pattern_name: str) -> List[Tuple[int, str]]:
    """Find all occurrences of a pattern in a file."""
    matches = []
    try:
        content = file_path.read_text(encoding="utf-8")
        for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
            line_num = content[:match.start()].count("\n") + 1
            matches.append((line_num, match.group(0)[:200]))  # First 200 chars
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
    return matches


def analyze_duplications(codebase_root: Path) -> Dict[str, List[Tuple[Path, int, str]]]:
    """Analyze codebase for common duplication patterns."""
    results = defaultdict(list)
    
    # Find all Python files
    python_files = list(codebase_root.rglob("*.py"))
    python_files = [f for f in python_files if "__pycache__" not in str(f)]
    
    print(f"Analyzing {len(python_files)} Python files...")
    
    for pattern, pattern_name in DUPLICATION_PATTERNS:
        print(f"  Checking pattern: {pattern_name}")
        pattern_results = []
        
        for py_file in python_files:
            matches = find_pattern_in_file(py_file, pattern, pattern_name)
            for line_num, match_content in matches:
                relative_path = py_file.relative_to(codebase_root)
                pattern_results.append((relative_path, line_num, match_content))
        
        if pattern_results:
            results[pattern_name] = pattern_results
    
    return results


def print_report(results: Dict[str, List[Tuple[Path, int, str]]]) -> None:
    """Print a formatted report of duplications."""
    print("\n" + "="*80)
    print("DUPLICATION ANALYSIS REPORT")
    print("="*80 + "\n")
    
    total_duplications = sum(len(matches) for matches in results.values())
    print(f"Total duplication patterns found: {total_duplications}\n")
    
    for pattern_name, matches in sorted(results.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n{pattern_name}:")
        print(f"  Found {len(matches)} occurrences")
        
        # Group by file
        by_file = defaultdict(list)
        for path, line_num, content in matches:
            by_file[path].append((line_num, content))
        
        print(f"  Across {len(by_file)} files")
        
        # Show top 5 files with most occurrences
        top_files = sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True)[:5]
        for file_path, file_matches in top_files:
            print(f"    {file_path}: {len(file_matches)} occurrences")


def main() -> None:
    """Main entry point."""
    if len(sys.argv) > 1:
        codebase_root = Path(sys.argv[1])
    else:
        codebase_root = Path(__file__).parent.parent
    
    if not codebase_root.exists():
        print(f"Error: {codebase_root} does not exist", file=sys.stderr)
        sys.exit(1)
    
    results = analyze_duplications(codebase_root)
    print_report(results)
    
    # Save detailed results to file
    output_file = codebase_root / "duplication_analysis.txt"
    with open(output_file, "w") as f:
        f.write("DETAILED DUPLICATION ANALYSIS\n")
        f.write("="*80 + "\n\n")
        for pattern_name, matches in sorted(results.items(), key=lambda x: len(x[1]), reverse=True):
            f.write(f"\n{pattern_name} ({len(matches)} occurrences):\n")
            f.write("-"*80 + "\n")
            for path, line_num, content in matches[:20]:  # First 20 per pattern
                f.write(f"{path}:{line_num}\n")
                f.write(f"  {content[:150]}...\n\n")
    
    print(f"\nDetailed report saved to: {output_file}")


if __name__ == "__main__":
    main()

