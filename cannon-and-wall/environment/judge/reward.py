FULL_POC_PATTERNS = {
    "sqli":        lambda p: "' OR 1=1" in p or "' OR '1'='1" in p,
    "xss":         lambda p: "<script>" in p.lower() and "alert" in p.lower(),
    "broken_auth": lambda p: "?user=admin" in p or "?user=" in p
}

def cannon_reward(report: dict, ground_truth: dict) -> float:
    score = 0.0
    if not all(report.get(k) for k in ["vuln_type","line_number","explanation","proof_of_concept"]):
        return -3.0
    vuln = report["vuln_type"]
    gt_vuln = ground_truth.get("vuln_type")
    if vuln != gt_vuln:
        return score - 5.0  # wrong type, stop scoring
    score += 5  # correct type
    lo, hi = ground_truth.get("line_number_range", [0, 0])
    if lo <= report.get("line_number", -1) <= hi:
        score += 5  # correct line range
    else:
        score -= 2
    # PoC must be a REAL full payload — not just keyword
    poc = report.get("proof_of_concept", "")
    if vuln in FULL_POC_PATTERNS and FULL_POC_PATTERNS[vuln](poc):
        score += 5
    else:
        score -= 5  # gibberish or single word = heavy penalty
    # explanation must mention the vuln word
    if vuln.replace("_","") not in report.get("explanation","").lower().replace("_",""):
        score -= 2
    return score

def wall_reward(patched_code: str, original_vulns: list, test_results: dict) -> float:
    score = 0.0
    if test_results.get("patch_valid"):
        score += 10
    if test_results.get("no_breakage"):
        score += 5
    score -= test_results.get("missed_vulns", 0) * 10
    score -= test_results.get("new_vulns", 0) * 5
    return score
