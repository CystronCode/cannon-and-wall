import subprocess, tempfile, os, ast, time, requests, shutil

VALID_VULN_TYPES = ["sqli", "xss", "broken_auth"]

def verify_cannon(report: dict) -> dict:
    issues = []
    for key in ["vuln_type", "line_number", "explanation", "proof_of_concept"]:
        if not report.get(key):
            issues.append(f"missing field: {key}")
    if report.get("vuln_type") not in VALID_VULN_TYPES:
        issues.append(f"invalid vuln_type: {report.get('vuln_type')}")
    vuln = report.get("vuln_type", "")
    poc = report.get("proof_of_concept", "")
    # PoC must contain a REAL exploit payload — not just a keyword
    VALID_POC = {
        "sqli":        lambda p: "' OR 1=1" in p or "' OR '1'='1" in p,
        "xss":         lambda p: "<script>" in p.lower() and "alert" in p.lower(),
        "broken_auth": lambda p: "?user=admin" in p or "?user=" in p
    }
    if vuln in VALID_POC and not VALID_POC[vuln](poc):
        issues.append(f"proof_of_concept is not a real {vuln} payload")
    return {"valid": len(issues) == 0, "issues": issues}

def _start_app(code: str, port: int = 15001) -> subprocess.Popen:
    tmpdir = tempfile.mkdtemp()
    app_path = os.path.join(tmpdir, "app.py")
    with open(app_path, "w") as f:
        f.write(code)
    proc = subprocess.Popen(
        ["python", app_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=tmpdir
    )
    time.sleep(2)  # wait for Flask to boot
    return proc, tmpdir

def _stop_app(proc, tmpdir):
    proc.terminate()
    proc.wait()
    shutil.rmtree(tmpdir, ignore_errors=True)

def _is_valid_python(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def verify_wall(patched_code: str, stage: int) -> dict:
    issues = []
    PORT = 15001

    # 1. Must be valid Python first
    if not _is_valid_python(patched_code):
        issues.append("patched_code is not valid Python")
        return {"valid": False, "patch_valid": False, "no_breakage": False,
                "missed_vulns": 1, "new_vulns": 0, "issues": issues}

    # 2. Boot the patched app in subprocess
    proc, tmpdir = _start_app(patched_code, PORT)
    base = f"http://localhost:{PORT}"

    try:
        # 3. Verify app is alive
        try:
            r = requests.get(f"{base}/health", timeout=3)
            if r.status_code != 200:
                issues.append("app did not boot — /health returned non-200")
                return {"valid": False, "patch_valid": False, "no_breakage": False,
                        "missed_vulns": 1, "new_vulns": 0, "issues": issues}
        except Exception:
            issues.append("app did not boot — /health unreachable")
            return {"valid": False, "patch_valid": False, "no_breakage": False,
                    "missed_vulns": 1, "new_vulns": 0, "issues": issues}

        # 4. SQLi check — send real injection payload
        sqli_fixed = True
        if stage in [1, 3]:
            r = requests.post(f"{base}/login",
                data={"username": "' OR 1=1--", "password": ""},
                timeout=3)
            if r.status_code == 200 and r.json().get("status") == "ok":
                issues.append("SQLi NOT fixed — injection payload returned 200 ok")
                sqli_fixed = False

        # 5. XSS check — send real XSS payload, response must escape it
        xss_fixed = True
        if stage in [2, 3]:
            r = requests.get(f"{base}/comments",
                params={"comment": "<script>alert(1)</script>"},
                timeout=3)
            if "<script>" in r.text:
                issues.append("XSS NOT fixed — raw <script> found in response")
                xss_fixed = False

        # 6. no_breakage — valid credentials must still work
        no_breakage = True
        r = requests.post(f"{base}/login",
            data={"username": "admin", "password": "password123"},
            timeout=3)
        if not (r.status_code == 200 and r.json().get("status") == "ok"):
            issues.append("no_breakage FAILED — valid login no longer works")
            no_breakage = False

    finally:
        _stop_app(proc, tmpdir)

    patch_valid = len(issues) == 0
    missed = 0
    if stage in [1,3] and not sqli_fixed: missed += 1
    if stage in [2,3] and not xss_fixed: missed += 1

    return {
        "valid": patch_valid,
        "patch_valid": patch_valid,
        "no_breakage": no_breakage,
        "missed_vulns": missed,
        "new_vulns": 0,
        "issues": issues
    }
