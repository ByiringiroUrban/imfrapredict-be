import os
import re

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

MOCK_PATTERNS = [
    (r"Math\.random\(\)", "Usage of Math.random() (often used for generating fake stats/metrics)"),
    (r"mock\w*", "Variables or strings containing 'mock' prefix/suffix"),
    (r"dummy\w*", "Variables or strings containing 'dummy'"),
    (r"const\s+\w+\s*=\s*\[\s*\{\s*\w+\s*:", "Inline mock object arrays (e.g. const tasks = [{ ... ])"),
    (r"setTimeout\(.*,\s*\d{3,4}\)", "Hardcoded setTimeout delays (often simulating network requests)"),
    (r"Lorem\s+ipsum", "Placeholder text (Lorem Ipsum)"),
]

EXCLUDE_DIRS = ["node_modules", "dist", "build", ".git"]

def audit_files():
    print("=" * 60)
    print("      INFRAPREDICT-AI WIRING & DUMMY DATA AUDIT TOOL      ")
    print("=" * 60)
    
    if not os.path.exists(FRONTEND_DIR):
        print(f"Error: Frontend directory not found at: {FRONTEND_DIR}")
        return

    findings = []
    total_files = 0
    
    for root, dirs, files in os.walk(FRONTEND_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file.endswith((".tsx", ".ts")):
                total_files += 1
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, FRONTEND_DIR)
                
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                except Exception as e:
                    print(f"Could not read {rel_path}: {e}")
                    continue
                
                for idx, line in enumerate(lines):
                    # Skip comments
                    clean_line = line.strip()
                    if clean_line.startswith(("//", "*", "/*")):
                        continue
                        
                    for pattern, desc in MOCK_PATTERNS:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Exempt known acceptable references or hooks
                            if "Math.random()" in line and "seed" in rel_path:
                                continue
                            if "DEMO_ORG_ID" in line or "import.meta.env" in line:
                                continue
                                
                            findings.append({
                                "file": rel_path,
                                "line": idx + 1,
                                "content": clean_line,
                                "desc": desc
                            })

    print(f"Scanned {total_files} frontend files.\n")
    
    if not findings:
        print("[SUCCESS] No dummy data indicators or unwired patterns found!")
        return

    print(f"[WARNING] Found {len(findings)} potential dummy/unwired items:\n")
    
    current_file = ""
    for f in sorted(findings, key=lambda x: (x["file"], x["line"])):
        if f["file"] != current_file:
            current_file = f["file"]
            print(f"\n[src/{current_file}]")
        print(f"   Line {f['line']:<4} | {f['desc']}")
        print(f"     Code: `{f['content']}`")
    
    print("\n" + "=" * 60)
    print("Audit Complete. Review the flagged lines above to verify wiring.")
    print("=" * 60)

if __name__ == "__main__":
    audit_files()
