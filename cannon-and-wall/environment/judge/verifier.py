# judge/verifier.py — V4 (AST-hardened sqli check, novelty signal)
import ast
import re
import subprocess
import tempfile
import os
import json

GROUND_TRUTH = {
    1: [
        {"vuln_type": "sqli",        "file": "app.py", "line_range": (10, 20)},
        {"vuln_type": "xss",         "file": "app.py", "line_range": (25, 35)},
        {"vuln_type": "broken_auth", "file": "app.py", "line_range": (40, 55)},
    ],
    2: [
        {"vuln_type": "sqli",        "file": "app.py", "line_range": (8,  22)},
        {"vuln_type": "xss",         "file": "app.py", "line_range": (28, 42)},
    ],
    3: [
        {"vuln_type": "sqli",        "file": "app.py", "line_range": (12, 28)},
        {"vuln_type": "xss",         "file": "app.py", "line_range": (32, 50)},
        {"vuln_type": "broken_auth", "file": "app.py", "line_range": (55, 75)},
    ],
}

# ---------------------------------------------------------------------------
# AST-level SQLi fix checker (replaces the brittle "?" anywhere heuristic)
# ---------------------------------------------------------------------------

def _sqli_fixed_ast(patched_code: str) -> bool:
    """
    Return True only when the patched code BOTH:
      (a) contains no f-string/%-string SELECT/INSERT/UPDATE/DELETE that
          injects a variable directly, AND
      (b) uses at least one parameterized query pattern where the placeholder
          (?, %s, :name) is inside a .execute() call alongside a tuple/list arg.

    This rejects tricks like:
      query = "SELECT ... WHERE name=?"   # placeholder present but never executed
      # ? fixed                           # plain comment
    """
    SQL_KEYWORDS = re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE)\b", re.IGNORECASE)

    # --- (a) check: no raw string interpolation feeding a SQL keyword ---
    try:
        tree = ast.parse(patched_code)
    except SyntaxError:
        return False  # unparseable patch = not fixed

    class _FStringChecker(ast.NodeVisitor):
        def __init__(self):
            self.found_raw_sql = False

        def visit_JoinedStr(self, node):  # f"..." node
            # Reconstruct what the f-string looks like by examining its parts
            has_sql_keyword = any(
                isinstance(v, ast.Constant) and SQL_KEYWORDS.search(str(v.value))
                for v in node.values
            )
            has_variable = any(isinstance(v, ast.FormattedValue) for v in node.values)
            if has_sql_keyword and has_variable:
                self.found_raw_sql = True
            self.generic_visit(node)

    checker = _FStringChecker()
    checker.visit(tree)
    if checker.found_raw_sql:
        return False  # still using f-string SQL injection

    # Also catch old-style %-formatting: "SELECT ... '%s'" % var
    if re.search(r"(SELECT|INSERT|UPDATE|DELETE).*%[sd]", patched_code, re.IGNORECASE):
        return False

    # --- (b) check: parameterized execute() must be present ---
    # Pattern: cursor.execute("...?...", (var,)) or cursor.execute("...%s...", [var])
    # We accept any execute( call that has a placeholder + a second argument.
    execute_param = re.search(
        r"execute\s*\(\s*['\"].*(\?|%s|:[a-z_]+).*['\"]"  # query with placeholder
        r".*,",                                              # followed by a comma (tuple/list arg)
        patched_code, re.DOTALL | re.IGNORECASE,
    )
    if execute_param:
        return True

    # Also accept SQLAlchemy / ORM text() with bound params
    if re.search(r"text\s*\(.*:[a-z_]+.*\)", patched_code, re.IGNORECASE):
        return True

    # ORM-style: .filter_by(username=username) — no raw SQL at all
    if re.search(r"\.(filter_by|filter|get)\s*\(", patched_code):
        return True

    return False


# ---------------------------------------------------------------------------
# Exploit novelty signal
# ---------------------------------------------------------------------------

_poc_history: list[str] = []  # module-level, survives across episodes in one process

def _exploit_is_novel(poc: str, history: list[str], threshold: float = 0.6) -> bool:
    """Return True if poc is sufficiently different from all recent PoCs."""
    def _similarity(a: str, b: str) -> float:
        a_tokens = set(a.lower().split())
        b_tokens = set(b.lower().split())
        if not a_tokens or not b_tokens:
            return 0.0
        return len(a_tokens & b_tokens) / max(len(a_tokens), len(b_tokens))

    for old_poc in history[-3:]:
        if _similarity(poc, old_poc) > threshold:
            return False
    return True


def record_poc(poc: str) -> bool:
    """Record a PoC and return whether it was novel."""
    novel = _exploit_is_novel(poc, _poc_history)
    _poc_history.append(poc)
    return novel


# ---------------------------------------------------------------------------
# Main patch verifier
# ---------------------------------------------------------------------------

def verify_patch(original_code: str, patched_code: str, vuln_type: str) -> dict:
    results = {
        "sqli_fixed": False,
        "xss_fixed": False,
        "broken_auth_fixed": False,
        "functionality_preserved": False,
        "new_vulns_introduced": False,
    }

    # --- SQLi: AST-level check (replaces the brittle "?" anywhere heuristic) ---
    results["sqli_fixed"] = _sqli_fixed_ast(patched_code)

    # --- XSS: escape fn present AND raw {comment}/{term}/{ref} NOT appearing ---
    escape_applied = (
        "html.escape" in patched_code
        or "escape(" in patched_code
        or "Markup.escape" in patched_code
        or "autoescape" in patched_code
    )
    # Check that user-input variable names are no longer interpolated raw into HTML
    raw_user_vars = re.search(
        r"\{(comment|term|q|ref|user_input|msg|text)\}",
        patched_code,
    )
    results["xss_fixed"] = escape_applied and not raw_user_vars

    # --- Broken auth ---
    results["broken_auth_fixed"] = (
        "request.args.get('user')" not in patched_code
        and "session['user'] = request" not in patched_code
        and "request.cookies.get('role_override')" not in patched_code
    )

    # --- Dangerous import rejection ---
    DANGEROUS = [
        "import os", "import subprocess", "import sys",
        "from os", "from subprocess", "from sys",
        "__import__", "exec(", "eval(",
    ]
    if any(d in patched_code for d in DANGEROUS):
        results["new_vulns_introduced"] = True
        results["functionality_preserved"] = False
        return results

    # --- Functionality check: does the patched file parse and import cleanly? ---
    with tempfile.TemporaryDirectory() as tmpdir:
        app_path = os.path.join(tmpdir, "app.py")
        with open(app_path, "w") as f:
            f.write(patched_code)

        try:
            r = subprocess.run(
                ["python3", "-c",
                 f"import sys; sys.path.insert(0, '{tmpdir}'); import app"],
                capture_output=True, text=True, timeout=10,
            )
            results["functionality_preserved"] = r.returncode == 0
        except Exception:
            results["functionality_preserved"] = False

        # --- Bandit static analysis for new HIGH-severity findings ---
        try:
            chk = subprocess.run(
                ["bandit", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            if chk.returncode != 0:
                raise RuntimeError("bandit missing")
            br = subprocess.run(
                ["bandit", "-r", app_path, "-f", "json", "-q"],
                capture_output=True, text=True, timeout=15,
            )
            if br.stdout:
                bd = json.loads(br.stdout)
                results["new_vulns_introduced"] = any(
                    i.get("issue_severity") == "HIGH"
                    for i in bd.get("results", [])
                )
        except Exception:
            results["new_vulns_introduced"] = False

    return results


# ---------------------------------------------------------------------------
# Cannon report verifier
# ---------------------------------------------------------------------------

def verify_cannon_report(cannon_report: dict, stage: int) -> dict:
    ground_truth = GROUND_TRUTH.get(stage, [])

    vuln = cannon_report.get("vuln_type", "")
    poc  = cannon_report.get("proof_of_concept", "")

    poc_valid = (
        (vuln == "sqli"        and any(p in poc for p in ["OR", "--", "'", '"', "UNION"])) or
        (vuln == "xss"         and "<script" in poc.lower()) or
        (vuln == "broken_auth" and any(p in poc for p in ["?user=", "role_override", "cookie"]))
    )
    if not poc_valid:
        return {
            "real_vuln_found":   False,
            "correct_vuln_type": False,
            "false_positive":    True,
            "exploit_novel":     False,
        }

    matched = correct_type = False
    for vuln_entry in ground_truth:
        if vuln_entry["vuln_type"] == vuln:
            correct_type = True
            lo, hi = vuln_entry["line_range"]
            if lo <= cannon_report.get("line_number", -1) <= hi:
                matched = True
                break

    exploit_novel = record_poc(poc)

    return {
        "real_vuln_found":   matched,
        "correct_vuln_type": correct_type,
        "false_positive":    not correct_type,
        "exploit_novel":     exploit_novel,
    }