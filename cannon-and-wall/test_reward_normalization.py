from environment.judge.reward import calculate_rewards

# Test 1 — perfect wall
r = calculate_rewards(
    {"real_vuln_found": True,  "correct_vuln_type": True,  "false_positive": False},
    {"sqli_fixed": True, "xss_fixed": True, "broken_auth_fixed": True,
     "functionality_preserved": True, "new_vulns_introduced": False},
    {"real_vuln_found": False, "correct_vuln_type": False, "false_positive": True})
assert 0.0 <= r["cannon_total"] <= 1.0, f"Cannon out of range: {r['cannon_total']}"
assert r["wall_total"] == 1.0, f"Perfect wall must be 1.0, got {r['wall_total']}"
print(f"✅ Test 1 — Cannon={r['cannon_total']} Wall={r['wall_total']}")

# Test 2 — worst-case wall (new vulns + bypassed)
r2 = calculate_rewards(
    {"real_vuln_found": False, "correct_vuln_type": False, "false_positive": True},
    {"sqli_fixed": False, "xss_fixed": False, "broken_auth_fixed": False,
     "functionality_preserved": False, "new_vulns_introduced": True},
    {"real_vuln_found": True, "correct_vuln_type": True, "false_positive": False})
# FIX (Issue F): was "== 0.0 or > 0.0" — always True, caught nothing
# Correct assertion:
assert 0.0 <= r2["wall_total"] <= 1.0, f"Wall out of range: {r2['wall_total']}"
assert r2["wall_total"] == 0.0, f"Worst wall must be 0.0, got {r2['wall_total']}"
print(f"✅ Test 2 — Cannon={r2['cannon_total']} Wall={r2['wall_total']}")

# Test 3 — worst-case cannon (hallucinates, never bypasses)
r3 = calculate_rewards(
    {"real_vuln_found": False, "correct_vuln_type": False, "false_positive": True},
    {"sqli_fixed": False, "xss_fixed": False, "broken_auth_fixed": False,
     "functionality_preserved": False, "new_vulns_introduced": False},
    {"real_vuln_found": False, "correct_vuln_type": False, "false_positive": True})
assert r3["cannon_total"] == 0.0, f"Worst cannon must be 0.0, got {r3['cannon_total']}"
assert 0.0 <= r3["wall_total"] <= 1.0, f"Wall out of range: {r3['wall_total']}"
print(f"✅ Test 3 — Cannon={r3['cannon_total']} Wall={r3['wall_total']}")

print("✅ All normalization assertions passed")
